import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

// Our Flask API is running on http://127.0.0.1:5000
const API_URL = "http://127.0.0.1:5000";

function App() {
  const [embedFile, setEmbedFile] = useState(null);
  const [watermarkText, setWatermarkText] = useState("");
  const [extractFile, setExtractFile] = useState(null);
  
  const [extractedMessage, setExtractedMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // --- Handlers for the EMBED section ---
  const handleEmbedFileChange = (e) => setEmbedFile(e.target.files[0]);
  const handleTextChange = (e) => setWatermarkText(e.target.value);

  const handleEmbedSubmit = async () => {
    if (!embedFile || !watermarkText) {
      setError("Please provide an image and watermark text.");
      return;
    }
    
    // Use FormData to send file and text
    const formData = new FormData();
    formData.append('image', embedFile);
    formData.append('text', watermarkText);

    setLoading(true);
    setError("");
    setExtractedMessage("");

    try {
      const response = await axios.post(`${API_URL}/embed`, formData, {
        responseType: 'blob', // We expect an image file back
      });

      // Create a URL for the returned image and trigger a download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'watermarked_image.png');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (err) {
      setError("An error occurred during embedding.");
    } finally {
      setLoading(false);
    }
  };

  // --- Handlers for the EXTRACT section ---
  const handleExtractFileChange = (e) => setExtractFile(e.target.files[0]);

  const handleExtractSubmit = async () => {
    if (!extractFile) {
      setError("Please provide an image to extract from.");
      return;
    }

    const formData = new FormData();
    formData.append('image', extractFile);

    setLoading(true);
    setError("");
    setExtractedMessage("");

    try {
      const response = await axios.post(`${API_URL}/extract`, formData);
      const message = response.data.message;

      if (message === "Could not find watermark.") {
        setError("No watermark found in this image.");
      } else {
        setExtractedMessage(`Found message: ${message}`);
      }
    } catch (err) {
      setError("An error occurred during extraction.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Robust Watermarking Tool</h1>
      </header>
      
      <div className="container">
        {/* --- EMBED SECTION --- */}
        <div className="card">
          <h2>1. Embed Watermark</h2>
          <input type="file" accept="image/png, image/jpeg" onChange={handleEmbedFileChange} />
          <input 
            type="text" 
            placeholder="Enter secret watermark..." 
            value={watermarkText} 
            onChange={handleTextChange} 
          />
          <button onClick={handleEmbedSubmit} disabled={loading}>
            {loading ? "Embedding..." : "Embed & Download"}
          </button>
        </div>

        {/* --- EXTRACT SECTION --- */}
        <div className="card">
          <h2>2. Extract Watermark</h2>
          <input type="file" accept="image/png, image/jpeg" onChange={handleExtractFileChange} />
          <button onClick={handleExtractSubmit} disabled={loading}>
            {loading ? "Extracting..." : "Extract Message"}
          </button>
        </div>
      </div>

      {/* --- RESULTS AREA --- */}
      <div className="results">
        {loading && <p className="loading">Processing...</p>}
        {error && <p className="error">{error}</p>}
        {extractedMessage && <p className="success">{extractedMessage}</p>}
      </div>
    </div>
  );
}

export default App;