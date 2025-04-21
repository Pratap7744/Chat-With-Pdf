import { useCallback, useState, useRef, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import '../styles/PdfUploader.css';
import QuestionForm from './QuestionForm';
import TypingIndicator from './TypingIndicator';

function PdfUploader() {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState('');
  const [isAnswering, setIsAnswering] = useState(false);
  const [pdfList, setPdfList] = useState([]);
  const [messages, setMessages] = useState([{
    id: 1, 
    text: 'No PDF is uploaded. Please upload a PDF to start chatting.', 
    sender: 'bot'
  }]);
  const [activePdf, setActivePdf] = useState(null);
  const [showUploadUI, setShowUploadUI] = useState(false);
  
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const processUploadedFile = async (file) => {
    if (file && file.type === 'application/pdf') {
      setLoading(true);
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const response = await axios.post('http://localhost:8000/upload-pdf', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        
        setUploadedFile(file.name);
        setActivePdf(file.name);
        
        // Add the file to the PDF list if not already present
        if (!pdfList.includes(file.name)) {
          setPdfList(prev => [...prev, file.name]);
        }
        setMessages([{ id: 1, text: `Uploaded ${file.name} successfully. Ask me anything!`, sender: 'bot' }]);
        
        // Hide the upload UI after successful upload
        setShowUploadUI(false);
      } catch (error) {
        console.error('Upload error:', error.response?.data || error.message);
        alert('Failed to upload PDF.');
      } finally {
        setLoading(false);
      }
    } else {
      alert('Please upload a valid PDF file.');
    }
  };

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    processUploadedFile(file);
  }, [pdfList]);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] }
  });

  useEffect(() => {
    if (answer) {
      setMessages(prev => [...prev, { id: Date.now(), text: answer, sender: 'bot' }]);
      setAnswer('');
    }
  }, [answer]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleNewMessage = async (message) => {
    // Add user message to chat
    const newMessageId = Date.now();
    setMessages(prev => [...prev, { id: newMessageId, text: message, sender: 'user' }]);
    
    // Show typing indicator
    setIsAnswering(true);
    
    // Process the message
    try {
      const payload = { query: message.trim(), num_chunks: 5 };
      const response = await axios.post('http://localhost:8000/ask-question', payload, {
        headers: { 'Content-Type': 'application/json' },
      });
      
      // Wait a bit before showing the response to let the typing indicator be visible
      setTimeout(() => {
        setAnswer(response.data.answer || response.data.message || 'No answer provided.');
        setIsAnswering(false);
      }, 1000);
    } catch (error) {
      const errorDetail = error.response?.data?.detail || error.message;
      setTimeout(() => {
        setAnswer(`Failed to get an answer: ${typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail, null, 2)}`);
        setIsAnswering(false);
      }, 1000);
    }
  };

  const handleSelectPdf = (pdfName) => {
    setActivePdf(pdfName);
    setUploadedFile(pdfName);
    setMessages([{ id: 1, text: `Loaded ${pdfName}. Ask me anything!`, sender: 'bot' }]);
    // Hide upload UI when selecting a PDF
    setShowUploadUI(false);
  };

  const handleUploadClick = () => {
    // Toggle the upload UI
    setShowUploadUI(true);
  };

  const handleChatClick = () => {
    // Hide upload UI and show chat
    setShowUploadUI(false);
  };

  const handleFileInput = (event) => {
    const file = event.target.files[0];
    if (file) {
      processUploadedFile(file);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="logo">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="40" height="40" rx="8" fill="#9333EA" />
            <path d="M28 12H12V28H28V12Z" fill="white" />
          </svg>
          <span>ChatWithPDF</span>
        </div>
        
        <div className="sidebar-content">
          {/* Upload New PDF link */}
          <div className={`sidebar-link ${showUploadUI ? 'active' : ''}`} onClick={handleUploadClick}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 5v9M12 5l-4 4M12 5l4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Upload New PDF</span>
          </div>
          
          {/* Chat with PDF link */}
          <div className={`sidebar-link ${!showUploadUI ? 'active' : ''}`} onClick={handleChatClick}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 11H4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M4 11V19C4 19.5304 4.21071 20.0391 4.58579 20.4142C4.96086 20.7893 5.46957 21 6 21H18C18.5304 21 19.0391 20.7893 19.4142 20.4142C19.7893 20.0391 20 19.5304 20 19V11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M12 3V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M8 7L12 3L16 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Chat with PDF</span>
          </div>
          
          {/* Hidden file input */}
          <input
            id="sidebar-file-input"
            type="file"
            accept="application/pdf"
            onChange={handleFileInput}
            ref={fileInputRef}
            style={{ display: 'none' }}
          />
          
          <div className="pdf-list-header">
            <span>Your PDFs</span>
          </div>
          
          <div className="pdf-list">
            {pdfList.length > 0 ? (
              pdfList.map((pdf, index) => (
                <div 
                  key={index} 
                  className={`pdf-item ${activePdf === pdf ? 'active' : ''}`}
                  onClick={() => handleSelectPdf(pdf)}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <span>{pdf}</span>
                </div>
              ))
            ) : (
              <div className="no-pdfs-message">No PDFs uploaded yet</div>
            )}
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="main-content">
        {showUploadUI ? (
          // Upload UI Section
          <div className="upload-section">
            <div className="content-header">
              <h1>Chat with <span className="pdf-highlight">PDF</span></h1>
              <p className="subtitle">
                Upload your PDF and ask questions to get instant answers from your documents
              </p>
            </div>
            <div className="upload-container" {...getRootProps()}>
              <input {...getInputProps()} id="file-upload-input" />
              <div className="upload-content">
                <div className="upload-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 5v9M12 5l-4 4M12 5l4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <p className="upload-text">Click to upload, or drag PDF here</p>
                
                <div className="upload-button-container">
                  <button className="upload-button">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 5v9M12 5l-4 4M12 5l4 4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    Upload PDF
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M19 9l-7 7-7-7" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          // Chat Interface
          <div className="chat-interface full-width">
            <div className="chat-header">
              <h2>{uploadedFile ? `Chatting with: ${uploadedFile}` : 'Chat with PDF'}</h2>
            </div>
            <div className="message-container" id="message-container">
              {messages.map(message => (
                <div key={message.id} className={`message-wrapper ${message.sender === 'bot' ? 'bot-message' : 'user-message'}`}>
                  <div className="message">
                    <p>{message.text}</p>
                  </div>
                </div>
              ))}
              
              {isAnswering && (
                <div className="message-wrapper bot-message">
                  <div className="message typing-message">
                    <TypingIndicator />
                  </div>
                </div>
              )}
              
              {/* Invisible div for auto-scrolling */}
              <div ref={messagesEndRef} />
            </div>
            <div className="chat-input-container">
              <QuestionForm onSendMessage={handleNewMessage} isDisabled={!uploadedFile} />
            </div>
          </div>
        )}
        
        {loading && (
          <div className="loading-overlay">
            <div className="loading-popup">
              <div className="spinner"></div>
              <p>Uploading PDF, please wait...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default PdfUploader;