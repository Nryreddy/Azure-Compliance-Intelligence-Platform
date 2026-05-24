const API_BASE_URL = 'http://localhost:8000';

export const submitVideoForAudit = async (videoUrl, videoName) => {
  try {
    const response = await fetch(`${API_BASE_URL}/audit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        video_url: videoUrl,
        video_name: videoName || null 
      }),
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return await response.json(); // Returns { session_id, message }
  } catch (error) {
    console.error("Error submitting video:", error);
    throw error;
  }
};

export const pollAuditStatus = async (sessionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/audit/${sessionId}`);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return await response.json(); // Returns { status, result, error }
  } catch (error) {
    console.error("Error polling status:", error);
    throw error;
  }
};

export const fetchAuditsHistory = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/audits`);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Error fetching history:", error);
    throw error;
  }
};

export const deleteAuditRecord = async (sessionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/audit/${sessionId}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Error deleting audit:", error);
    throw error;
  }
};

export const fetchKBFiles = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/knowledge/files`);
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching KB files:", error);
    throw error;
  }
};

export const uploadKBFile = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/knowledge/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `API Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error uploading KB file:", error);
    throw error;
  }
};

export const deleteKBFile = async (filename) => {
  try {
    const response = await fetch(`${API_BASE_URL}/knowledge/files/${encodeURIComponent(filename)}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `API Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error deleting KB file:", error);
    throw error;
  }
};
