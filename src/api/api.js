import axios from "axios";

export const getAIMessage = async (userQuery) => {
  try {
    const res = await axios.post(`http://localhost:5000/api`, {query: userQuery});
  
    if (res.status !== 200) {
      throw new Error('Failed to fetch');
    }
  
    const resData = res.data;
    console.log(resData);
    const content = resData.content;
  
    const message = 
      {
        role: "assistant",
        content: content
      }
  
    return message;
  }
  catch (error) {
    console.error('Error fetching from backend:', error);
    return {
      role: "assistant",
      content: "error"
    }
  }
};
