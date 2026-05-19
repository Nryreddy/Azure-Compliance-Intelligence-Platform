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
