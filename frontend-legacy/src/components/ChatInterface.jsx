import React, { useState } from 'react';

const ChatInterface = ({ agentName, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Function to format message content with tool usage
  const formatMessage = (text) => {
    // Check if the message contains web search results
    if (text.includes("[web_search_results]") || text.includes("Search results:")) {
      return formatWebSearchResults(text);
    }
    
    // Check if the message contains tool usage indicators
    if (text.includes("I'll use the") || text.includes("Using the")) {
      // Split the text by lines
      const lines = text.split('\n');
      return lines.map((line, i) => {
        // Highlight tool usage
        if (line.includes("I'll use the") || line.includes("Using the")) {
          return <div key={i} className="font-semibold text-blue-600">{line}</div>;
        }
        // Highlight tool results
        else if (line.includes("Result:") || line.includes("Tool result:")) {
          return <div key={i} className="pl-2 border-l-2 border-green-500 text-green-700">{line}</div>;
        }
        return <div key={i}>{line}</div>;
      });
    }
    
    // If no tool usage detected, return the text as is
    return text;
  };

  // Function to format web search results
  const formatWebSearchResults = (text) => {
    // Try to identify web search results section
    const beforeSearch = text.split(/\[web_search_results\]|Search results:/)[0];
    let searchResults = "";
    let afterSearch = "";
    
    if (text.includes("[web_search_results]")) {
      const parts = text.split("[web_search_results]");
      if (parts.length > 1) {
        searchResults = parts[1].split("[/web_search_results]")[0];
        afterSearch = parts[1].split("[/web_search_results]")[1] || "";
      }
    } else if (text.includes("Search results:")) {
      const parts = text.split("Search results:");
      if (parts.length > 1) {
        // Try to find where the search results end
        const endMarkers = ["Based on these results", "According to the search", "From the search"];
        let endIndex = -1;
        
        for (const marker of endMarkers) {
          const idx = parts[1].indexOf(marker);
          if (idx !== -1 && (endIndex === -1 || idx < endIndex)) {
            endIndex = idx;
          }
        }
        
        if (endIndex !== -1) {
          searchResults = parts[1].substring(0, endIndex);
          afterSearch = parts[1].substring(endIndex);
        } else {
          // If no end marker found, assume the entire rest is search results
          searchResults = parts[1];
        }
      }
    }
    
    return (
      <>
        {beforeSearch}
        {searchResults && (
          <div className="my-2 p-2 bg-gray-50 border border-gray-200 rounded">
            <div className="text-sm font-semibold text-gray-700 mb-1">Web Search Results:</div>
            <div className="text-sm text-gray-600 whitespace-pre-line">{searchResults}</div>
          </div>
        )}
        {afterSearch}
      </>
    );
  };

  const handleSendMessage = async () => {
    if (!input.trim()) return;
    
    // Add user message to chat
    const userMessage = { sender: 'user', text: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setIsLoading(true);
    
    try {
      // Call API to interact with agent
      const response = await fetch(`http://localhost:8000/interact/${agentName}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
      });
      
      const data = await response.json();
      
      // Add agent response to chat
      setMessages(prev => [...prev, { sender: 'agent', text: data.response }]);
    } catch (error) {
      console.error('Error interacting with agent:', error);
      setMessages(prev => [...prev, { 
        sender: 'system', 
        text: 'Error: Could not connect to the agent. Please try again.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl h-3/4 flex flex-col">
        <div className="bg-gray-800 text-white p-4 rounded-t-lg flex justify-between items-center">
          <h2 className="text-xl font-bold">Chat with {agentName}</h2>
          <button 
            onClick={onClose}
            className="text-white hover:text-gray-300"
          >
            ✕
          </button>
        </div>
        
        <div className="flex-1 p-4 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-10">
              Start a conversation with {agentName}
            </div>
          ) : (
            messages.map((msg, index) => (
              <div 
                key={index} 
                className={`message-container mb-4 ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}
              >
                <div 
                  className={`inline-block p-3 rounded-lg ${
                    msg.sender === 'user' 
                      ? 'bg-blue-500 text-white' 
                      : msg.sender === 'system'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-200 text-gray-800'
                  }`}
                >
                  {msg.sender === 'agent' ? formatMessage(msg.text) : msg.text}
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="message-container text-left mb-4">
              <div className="inline-block p-3 rounded-lg bg-gray-200 text-gray-800">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>
        
        <div className="p-4 border-t">
          <div className="flex">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Type your message..."
              className="flex-1 p-2 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSendMessage}
              disabled={isLoading}
              className="bg-blue-500 text-white px-4 py-2 rounded-r-lg hover:bg-blue-600 transition disabled:bg-blue-300"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface; 