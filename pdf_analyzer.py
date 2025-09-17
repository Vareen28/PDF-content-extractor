"""
PDF Analyzer Module - Provides text analysis and understanding capabilities
"""

import os
import re
import logging
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import Counter, defaultdict
import math
import json
import importlib.util
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to download NLTK data
def download_nltk_data():
    """Download required NLTK data packages."""
    try:
        # Create nltk_data directory in user home if it doesn't exist
        nltk_data_path = os.path.join(os.path.expanduser("~"), "nltk_data")
        os.makedirs(nltk_data_path, exist_ok=True)
        
        # Add the custom path
        nltk.data.path.append(nltk_data_path)
        
        # Download required packages
        resources = ['punkt', 'stopwords']
        for resource in resources:
            try:
                nltk.download(resource, quiet=True, download_dir=nltk_data_path)
                logger.info(f"Downloaded NLTK resource: {resource}")
            except Exception as e:
                logger.error(f"Error downloading NLTK resource {resource}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error setting up NLTK data: {str(e)}")

# Download NLTK data at module load time
download_nltk_data()

class PDFAnalyzer:
    def __init__(self, text_content=None):
        """Initialize the analyzer with optional text content."""
        self.text_content = text_content
        self.sentences = []
        self.keywords = []
        self.summary = ""
        self.topics = {}
        self.entities = []
        self.use_openai = False
        self.nltk_available = True
        
        # Verify NLTK resources
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError as e:
            logger.error(f"NLTK resources not available: {str(e)}")
            logger.info("Trying to download missing NLTK resources...")
            download_nltk_data()
            
            # Check again
            try:
                nltk.data.find('tokenizers/punkt')
                nltk.data.find('corpora/stopwords')
            except LookupError:
                logger.error("Failed to download NLTK resources. Advanced text analysis will be limited.")
                self.nltk_available = False
        
        # Check if LangChain and OpenAI modules are available
        if importlib.util.find_spec("langchain") and importlib.util.find_spec("langchain_openai"):
            try:
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.use_openai = True
                    logger.info("OpenAI integration available")
            except Exception as e:
                logger.warning(f"OpenAI API key not found or error loading: {str(e)}")
                
    def set_text(self, text_content):
        """Set the text content to analyze."""
        self.text_content = text_content
        self.sentences = []
        self.keywords = []
        self.summary = ""
        self.topics = {}
        self.entities = []
    
    def preprocess_text(self):
        """Preprocess the text content for analysis."""
        if not self.text_content:
            logger.error("No text content to analyze")
            return False
        
        if not self.nltk_available:
            # Simple fallback for sentence splitting if NLTK is not available
            self.sentences = [s.strip() for s in self.text_content.split('.') if s.strip()]
            logger.info(f"Used basic sentence splitting, extracted {len(self.sentences)} sentences")
            return bool(self.sentences)
            
        try:
            # Tokenize the text into sentences
            self.sentences = sent_tokenize(self.text_content)
            logger.info(f"Extracted {len(self.sentences)} sentences")
            return True
        except Exception as e:
            logger.error(f"Error preprocessing text: {str(e)}")
            # Fallback to basic sentence splitting
            self.sentences = [s.strip() for s in self.text_content.split('.') if s.strip()]
            logger.info(f"Fallback: Basic sentence splitting, extracted {len(self.sentences)} sentences")
            return bool(self.sentences)
    
    def extract_keywords(self, top_n=20):
        """Extract the most important keywords from the text."""
        if not self.text_content:
            logger.error("No text content to analyze")
            return []
        
        if not self.nltk_available:
            # Simple fallback for keyword extraction
            words = self.text_content.lower().split()
            # Filter out short words
            words = [w for w in words if len(w) > 3]
            # Count frequencies
            word_freq = Counter(words)
            # Get most common words
            self.keywords = [word for word, count in word_freq.most_common(top_n)]
            logger.info(f"Used basic keyword extraction, found {len(self.keywords)} keywords")
            return self.keywords
            
        try:
            # Tokenize and filter stopwords
            stop_words = set(stopwords.words('english'))
            words = word_tokenize(self.text_content.lower())
            filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
            
            # Count word frequencies
            word_freq = Counter(filtered_words)
            
            # Get the most common words
            self.keywords = [word for word, count in word_freq.most_common(top_n)]
            logger.info(f"Extracted {len(self.keywords)} keywords")
            return self.keywords
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            # Fallback to simpler method
            words = self.text_content.lower().split()
            words = [w for w in words if len(w) > 3]
            word_freq = Counter(words)
            self.keywords = [word for word, count in word_freq.most_common(top_n)]
            logger.info(f"Fallback: Basic keyword extraction, found {len(self.keywords)} keywords")
            return self.keywords
    
    def generate_summary(self, sentences_count=5):
        """Generate a summary using TF-IDF approach."""
        if not self.sentences:
            self.preprocess_text()
            if not self.sentences:
                return ""
                
        try:
            # Calculate term frequencies
            word_freq = defaultdict(int)
            for sentence in self.sentences:
                for word in word_tokenize(sentence.lower()):
                    if word.isalnum():
                        word_freq[word] += 1
                        
            # Calculate sentence scores based on word frequencies
            sentence_scores = defaultdict(float)
            for i, sentence in enumerate(self.sentences):
                for word in word_tokenize(sentence.lower()):
                    if word.isalnum():
                        sentence_scores[i] += word_freq[word]
                        
                # Normalize by sentence length
                sentence_scores[i] = sentence_scores[i] / max(1, len(word_tokenize(sentence)))
                
            # Get the top sentences
            top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:sentences_count]
            top_sentences = sorted(top_sentences, key=lambda x: x[0])  # Sort by original position
            
            # Create the summary
            self.summary = " ".join([self.sentences[i] for i, _ in top_sentences])
            logger.info(f"Generated summary of {len(top_sentences)} sentences")
            return self.summary
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return ""
    
    def extract_topics(self, max_topics=5):
        """Extract main topics from the text using simple clustering."""
        if not self.keywords:
            self.extract_keywords(top_n=50)
            
        try:
            # Group related keywords
            topics = {}
            used_keywords = set()
            
            for i, keyword in enumerate(self.keywords):
                if keyword in used_keywords:
                    continue
                    
                # Start a new topic
                related_words = [keyword]
                used_keywords.add(keyword)
                
                # Find co-occurring words
                for other_keyword in self.keywords:
                    if other_keyword not in used_keywords:
                        # Simple co-occurrence check
                        window_size = 50  # characters
                        pattern = r'.{0,%d}%s.{0,%d}%s.{0,%d}' % (
                            window_size, re.escape(keyword), window_size, 
                            re.escape(other_keyword), window_size
                        )
                        if re.search(pattern, self.text_content.lower()):
                            related_words.append(other_keyword)
                            used_keywords.add(other_keyword)
                            
                if len(related_words) > 1:  # Only add topics with multiple related words
                    topics[keyword] = related_words
                    
                if len(topics) >= max_topics:
                    break
                    
            self.topics = topics
            logger.info(f"Extracted {len(topics)} topics")
            return topics
        except Exception as e:
            logger.error(f"Error extracting topics: {str(e)}")
            return {}
    
    def analyze_sentiment(self):
        """Perform basic sentiment analysis."""
        if not self.text_content:
            logger.error("No text content to analyze")
            return {"positive": 0, "negative": 0, "neutral": 0}
            
        try:
            # Basic lexicon-based approach
            positive_words = {"good", "great", "excellent", "positive", "best", "better", 
                             "advantage", "benefit", "success", "successful", "improve",
                             "improved", "improvement", "recommended", "recommend"}
            negative_words = {"bad", "poor", "negative", "worst", "worse", "disadvantage",
                             "problem", "issue", "fault", "fail", "failed", "failure",
                             "difficult", "difficulty", "concern", "concerns"}
            
            # Count sentiment words
            words = word_tokenize(self.text_content.lower())
            pos_count = sum(1 for word in words if word in positive_words)
            neg_count = sum(1 for word in words if word in negative_words)
            
            # Calculate percentages
            total_sentiment_words = pos_count + neg_count
            if total_sentiment_words == 0:
                return {"positive": 0, "negative": 0, "neutral": 100}
                
            pos_percent = (pos_count / total_sentiment_words) * 100
            neg_percent = (neg_count / total_sentiment_words) * 100
            
            sentiment = {
                "positive": round(pos_percent, 1),
                "negative": round(neg_percent, 1),
                "neutral": round(100 - pos_percent - neg_percent, 1)
            }
            
            logger.info(f"Sentiment analysis completed: {sentiment}")
            return sentiment
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {"positive": 0, "negative": 0, "neutral": 0}
    
    def answer_question(self, question):
        """Answer a question about the text content."""
        if not self.text_content:
            return "No text content has been loaded."
            
        if self.use_openai:
            try:
                # Use LangChain with OpenAI for question answering
                from langchain_openai import ChatOpenAI
                from langchain.schema import HumanMessage, SystemMessage
                
                # Initialize the model
                model = ChatOpenAI(model="gpt-3.5-turbo")
                
                # Create the prompt
                system_prompt = "You are a helpful assistant that answers questions about a PDF document's content."
                
                # Truncate text if too long (token limit consideration)
                max_length = 8000
                text_to_use = self.text_content[:max_length] if len(self.text_content) > max_length else self.text_content
                if len(self.text_content) > max_length:
                    text_to_use += "... [document truncated due to length]"
                
                # Combine the question with content
                user_prompt = f"Document content:\n\n{text_to_use}\n\nQuestion: {question}"
                
                # Get the answer
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                response = model.invoke(messages)
                return response.content
                
            except Exception as e:
                logger.error(f"Error using OpenAI for question answering: {str(e)}")
                logger.info("Falling back to basic question answering")
        
        # Basic keyword matching answer
        try:
            question = question.lower()
            question_words = set(word_tokenize(question)) - set(stopwords.words('english'))
            
            # Find sentences with the most question keywords
            sentence_scores = []
            for i, sentence in enumerate(self.sentences):
                sentence_words = set(word_tokenize(sentence.lower()))
                # Calculate score based on keyword matches
                score = sum(1 for word in question_words if word in sentence_words)
                if score > 0:
                    sentence_scores.append((i, score, sentence))
            
            # Sort by score and return top matches
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            
            if not sentence_scores:
                return "I couldn't find information related to that question in the document."
            
            # Return top 2-3 matching sentences
            top_matches = sentence_scores[:3]
            answers = [sentence for _, _, sentence in top_matches]
            return " ".join(answers)
            
        except Exception as e:
            logger.error(f"Error in basic question answering: {str(e)}")
            return "I encountered an error trying to answer that question."
    
    def get_analysis_results(self):
        """Get a complete analysis of the text content."""
        if not self.text_content:
            return {"error": "No text content has been loaded."}
            
        # Run all analysis methods if not already done
        if not self.sentences:
            self.preprocess_text()
        if not self.keywords:
            self.extract_keywords()
        if not self.summary:
            self.generate_summary()
        if not self.topics:
            self.extract_topics()
            
        # Compile the results
        sentiment = self.analyze_sentiment()
        
        results = {
            "summary": self.summary,
            "keywords": self.keywords[:10],  # Top 10 keywords
            "topics": self.topics,
            "sentiment": sentiment,
            "stats": {
                "sentences": len(self.sentences),
                "words": len(word_tokenize(self.text_content)),
                "characters": len(self.text_content)
            }
        }
        
        return results 