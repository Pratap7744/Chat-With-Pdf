import { useState } from 'react';
import '../styles/QuestionForm.css';

function QuestionForm({ onSendMessage }) {
  const [query, setQuery] = useState('');
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      return;
    }
    
    // Pass the message to parent component
    onSendMessage(query);
    
    // Clear the input
    setQuery('');
  };
  
  return (
    <form onSubmit={handleSubmit} className="question-form">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask a question about your PDF..."
        className="question-input"
      />
      <button 
        type="submit" 
        disabled={!query.trim()} 
        className="send-button"
        aria-label="Send message"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M22 2L11 13" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>
    </form>
  );
}

export default QuestionForm;