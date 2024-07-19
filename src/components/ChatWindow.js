import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./ChatWindow.css";
import { getAIMessage } from "../api/api";
import { marked } from "marked";

function ChatWindow() {

  /* const defaultMessage = [{
    role: "system",
    content: "Hi, how can I help you today?"
  }]; */
  const [isLoading, setIsLoading] = useState(false);
  const [messages,setMessages] = useState([]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get("http://localhost:5000/api/initial");
        const initial_message = res.data;
        setMessages([initial_message]);
      } catch (error) {
        console.error("Error fetching initial message:", error);
      }
    };
    fetchData();
  }, []) 

  useEffect(() => {
      scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (input.trim() !== "") {
      // Set user message
      setMessages(prevMessages => [...prevMessages, { role: "user", content: input }]);
      setInput("");

      // Call API & set assistant message
      setIsLoading(true);
      const newMessage = await getAIMessage(input);
      setMessages(prevMessages => [...prevMessages, newMessage]);
      setIsLoading(false);
    }
  };

  return (
      <div className="messages-container">

          {messages.map((message, index) => (
              <div key={index} className={`${message.role}-message-container`}>
                  {message.content && (
                      <div className={`message ${message.role}-message`}>
                          <div dangerouslySetInnerHTML={{__html: marked(message.content).replace(/<p>|<\/p>/g, "")}}></div>
                      </div>
                  )}
              </div>
          ))}
          <div ref={messagesEndRef}>
          {isLoading ? <div class="typing">
            <span></span><span></span><span></span>
          </div> : null}
          </div>
          

          <div className="input-area">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              onKeyPress={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  handleSend(input);
                  e.preventDefault();
                }
              }}
              rows="3"
            />
            <button className="send-button" onClick={handleSend}>
              Send
            </button>
          </div>
      </div>
);
}

export default ChatWindow;
