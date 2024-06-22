import numpy as np
import requests
import logging
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Conv1D, GlobalMaxPooling1D, Dense
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

def fetch_real_time_sentiment():
    response = requests.get('https://api.example.com/sentiment')
    if response.status_code == 200:
        sentiment_data = response.json()
        sentiment_score = sentiment_data['score']
        logging.info(f"Real-time sentiment score: {sentiment_score}")
        return sentiment_score
    else:
        logging.error(f"Failed to fetch sentiment data: {response.status_code}")
        return None

def preprocess_text(tweets):
    tokenizer = Tokenizer(num_words=5000)
    tokenizer.fit_on_texts(tweets)
    sequences = tokenizer.texts_to_sequences(tweets)
    data = pad_sequences(sequences, maxlen=100)
    return data, tokenizer

def build_sentiment_model(input_length):
    model = Sequential()
    model.add(Embedding(input_dim=5000, output_dim=128))
    model.add(Conv1D(128, 5, activation='relu'))
    model.add(GlobalMaxPooling1D())
    model.add(Dense(10, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

def analyze_sentiment(tweets, model, tokenizer):
    data, _ = preprocess_text(tweets)
    predictions = model.predict(data)
    return np.mean(predictions)

# Example usage (assuming you have a trained model and tokenizer)
if __name__ == "__main__":
    # Dummy data for demonstration (replace with your actual data)
    tweets = ["I love this!", "I hate this!", "This is the best!", "This is the worst!"]
    labels = [1, 0, 1, 0]  # 1 for positive, 0 for negative

    data, tokenizer = preprocess_text(tweets)
    label_encoder = LabelEncoder()
    labels = label_encoder.fit_transform(labels)

    # Split the data into training and validation sets
    X_train, X_val, y_train, y_val = train_test_split(data, labels, test_size=0.2, random_state=42)

    model = build_sentiment_model(X_train.shape[1])

    # Train the model with validation
    model.fit(X_train, y_train, epochs=10, batch_size=2, validation_data=(X_val, y_val))

    # Analyze sentiment on new tweets
    new_tweets = ["This is amazing!", "This is terrible!"]
    average_sentiment = analyze_sentiment(new_tweets, model, tokenizer)
    print(f"Average sentiment score: {average_sentiment}")
