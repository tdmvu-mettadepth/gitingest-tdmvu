import torch
from transformers import BertTokenizer, BertModel
from rapidfuzz import fuzz


class NLIModel(torch.nn.Module):
    def __init__(self, bert_model_name="bert-base-uncased"):
        super(NLIModel, self).__init__()
        self.bert = BertModel.from_pretrained(bert_model_name)

        # Assuming BERT output dimension is 768
        self.attention = torch.nn.MultiheadAttention(embed_dim=768, num_heads=8)
        self.feed_forward = torch.nn.Sequential(
            torch.nn.Linear(768, 512),
            torch.nn.ReLU(),
            torch.nn.Linear(512, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, 1)
        )
        self.sigmoid = torch.nn.Sigmoid()

    def forward(self, input_ids, attention_mask):
        bert_output = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = bert_output.last_hidden_state[:, 0, :]  # Use [CLS] token
        # Apply attention
        attn_output, _ = self.attention(pooled_output.unsqueeze(0), pooled_output.unsqueeze(0), pooled_output.unsqueeze(0))
        attn_output = attn_output.squeeze(0)
        # Feed forward
        output = self.feed_forward(attn_output)
        # Sigmoid activation
        return self.sigmoid(output)

class ColumnMapper():
    def __init__(self, bert_model_name='app/models/best_model.pth'):
        self.model = NLIModel()
        self.model.load_state_dict(torch.load(bert_model_name, map_location=torch.device('cpu')))
        self.model.eval()
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        self.column_mapping_template = {'incoming_column': '', 'best_match': '', 'score': 0}
        
    def predict_score(self, query, passage, max_length=512):
        encoding = self.tokenizer.encode_plus(
            query,
            passage,
            add_special_tokens=True,
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        input_ids = encoding['input_ids']
        attention_mask = encoding['attention_mask']

        with torch.no_grad():
            output = self.model(input_ids, attention_mask)

        return output.item()

    def get_best_match(self, query, candidates):
        results = []
        for candidate in candidates:
            score = self.predict_score(query, candidate)
            results.append((candidate, score))

        # Sort results by score in descending order
        results.sort(key=lambda x: x[1], reverse=True)
        return results[0]

    def fuzzy_candidates(self, query, candidates, threshold=70, max_candidates=6):
        results = []
        # print(query, candidates)
        for candidate in candidates:
            similarity_score = fuzz.ratio(query.lower(), candidate.lower())
            if similarity_score >= threshold:  # Filter based on similarity
                results.append((candidate, similarity_score))
                if len(results) >= max_candidates:  # Limit to max_candidates
                    break
        return results

    def map_columns(self, incoming_column, standard_column):
        response = []
        # column_mapping_template = {'incoming_column': '', 'best_match': '', 'score': 0}
        for query in incoming_column:
            column_mapping = self.column_mapping_template.copy()
            # Get candidates using fuzzy matching
            candidates = self.fuzzy_candidates(query, standard_column)

            # If no candidates found, print a message and mark field as required
            if not candidates:
                column_mapping['incoming_column'] = query
                column_mapping['best_match'] = "Required field (no candidates found)"
                column_mapping['score'] = 0
                response.append(column_mapping) 
                # response[query] = {"match": "Required field (no candidates found)", "score": 0}
                # print(f"{query} : Required field (no candidates found)")
                continue

            # Now, predict scores for the candidates
            scores = []
            for candidate, _ in candidates:
                score = self.predict_score(query, candidate)
                scores.append((candidate, score))

            # Sort scores by descending order
            scores.sort(key=lambda x: x[1], reverse=True)

            # Output the best match and its score
            best_match, best_score = scores[0]
            if best_score < 0.1:
                column_mapping['incoming_column'] = query
                column_mapping['best_match'] = "Required field (no candidates found)"
                column_mapping['score'] = 0
                response.append(column_mapping)
                # response[query] = {"match": "Required field (no candidates found)", "score": 0}
                # print(f"{query} : Required field (no candidates found)")
            else:
                column_mapping['incoming_column'] = query
                column_mapping['best_match'] = best_match
                column_mapping['score'] = best_score
                response.append(column_mapping)
                # response[query] = {"match": best_match, "score": best_score}
                # print(f"{query} : {best_match} : {best_score:.4f}")
        return response
    