import { useState } from 'react';
import PdfUploader from './components/PdfUploader';
import QuestionForm from './components/QuestionForm';
import './styles/App.css';
import './index.css';

function App() {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  return (
    <div className="app-container">
      <div className="card">
        <PdfUploader setUploadedFile={setUploadedFile} setLoading={setLoading} />
        {uploadedFile && (
          <>
            <QuestionForm setAnswer={setAnswer} setLoading={setLoading} />
          </>
        )}
      </div>
    </div>
  );
}

export default App;