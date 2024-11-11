from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from typing import Dict, List, Tuple
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

class BidirectionalTranslator:
    def __init__(self, csv_file: str):
        """
        Initialize the translator with a CSV file containing translations.
        
        Args:
            csv_file (str): Path to the CSV file with 'chakma' and 'bangla' columns
        """
        self.df = pd.read_csv(csv_file)
        self.chakma_to_bangla = {}
        self.bangla_to_chakma = {}
        self._build_dictionaries()
    
    def _build_dictionaries(self):
        """Build bidirectional dictionaries from the CSV data, handling synonyms."""
        for _, row in self.df.iterrows():
            # Handle multiple translations (synonyms) separated by commas
            chakma_words = [word.strip() for word in str(row['chakma']).split(',')]
            bangla_words = [word.strip() for word in str(row['bangla']).split(',')]
            
            # Add all combinations to both dictionaries
            for chakma in chakma_words:
                if chakma:
                    self.chakma_to_bangla[chakma.lower()] = bangla_words
            
            for bangla in bangla_words:
                if bangla:
                    self.bangla_to_chakma[bangla.lower()] = bangla_words
    
    def translate_word(self, word: str, to_bangla: bool = True) -> List[str]:
        """
        Translate a single word.
        
        Args:
            word (str): Word to translate
            to_bangla (bool): If True, translate from Chakma to Bangla; if False, vice versa
            
        Returns:
            List[str]: List of possible translations (including synonyms)
        """
        word = word.lower()
        dictionary = self.chakma_to_bangla if to_bangla else self.bangla_to_chakma
        return dictionary.get(word, [word])  # Return original word if no translation found
    
    def translate_sentence(self, sentence: str, to_bangla: bool = True) -> Tuple[str, str]:
        """
        Translate a sentence word by word.
        
        Args:
            sentence (str): Sentence to translate
            to_bangla (bool): If True, translate from Chakma to Bangla; if False, vice versa
            
        Returns:
            Tuple[str, str]: (Primary translation, Alternative translations)
        """
        words = sentence.split()
        primary_translation = []
        all_possibilities = []
        
        for word in words:
            translations = self.translate_word(word, to_bangla)
            # Use first translation as primary
            primary_translation.append(translations[0])
            # Store all possible translations
            if len(translations) > 1:
                all_possibilities.append(f"{word}: {', '.join(translations)}")
        
        primary = ' '.join(primary_translation)
        alternatives = all_possibilities if all_possibilities else ["No alternative translations"]
        
        return primary, alternatives

# Initialize the translator
# csv_path = os.getenv('DICTIONARY_PATH', 'https://gist.githubusercontent.com/junechakma/39b280baa4f01ea599b65f5c91cdbe60/raw/0eafe0ec3866e491ab1758b6d897d19799ae7b5b/gistfile1.csv')
translator = BidirectionalTranslator('https://gist.githubusercontent.com/junechakma/39b280baa4f01ea599b65f5c91cdbe60/raw/0eafe0ec3866e491ab1758b6d897d19799ae7b5b/gistfile1.csv')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Translation service is running'
    })

@app.route('/translate/word', methods=['POST'])
def translate_word():
    """
    Endpoint for translating a single word
    
    Expected JSON payload:
    {
        "text": "word_to_translate",
        "to_bangla": true
    }
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing required field: text'
            }), 400

        text = data['text'].strip()
        to_bangla = data.get('to_bangla', True)

        if not text:
            return jsonify({
                'error': 'Empty text provided'
            }), 400

        translations = translator.translate_word(text, to_bangla)
        
        return jsonify({
            'text': text,
            'primary_translation': translations[0],
            'alternative_translations': translations[1:] if len(translations) > 1 else [],
            'direction': 'chakma_to_bangla' if to_bangla else 'bangla_to_chakma'
        })

    except Exception as e:
        return jsonify({
            'error': f'Translation failed: {str(e)}'
        }), 500

@app.route('/translate/sentence', methods=['POST'])
def translate_sentence():
    """
    Endpoint for translating a sentence
    
    Expected JSON payload:
    {
        "text": "sentence to translate",
        "to_bangla": true
    }
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing required field: text'
            }), 400

        text = data['text'].strip()
        to_bangla = data.get('to_bangla', True)

        if not text:
            return jsonify({
                'error': 'Empty text provided'
            }), 400

        primary, alternatives = translator.translate_sentence(text, to_bangla)
        
        return jsonify({
            'text': text,
            'primary_translation': primary,
            'alternative_translations': alternatives,
            'direction': 'chakma_to_bangla' if to_bangla else 'bangla_to_chakma'
        })

    except Exception as e:
        return jsonify({
            'error': f'Translation failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)