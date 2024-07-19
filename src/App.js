import React from "react";
import ReactDOM from "react-dom";
import "./App.css";
import ChatWindow from "./components/ChatWindow";

const App = () => {
  return (
    <React.StrictMode>
      <div className="App">
        <div className="heading">
          Instalily Case Study
        </div>
          <ChatWindow/>
      </div>
    </React.StrictMode>
  )
}

ReactDOM.render(
  <App />,
  document.getElementById('root')
);

/* 
function App() {

  return (
    <div className="App">
      <div className="heading">
        Instalily Case Study
      </div>
        <ChatWindow/>
    </div>
  );
}

export default App; */
export default App;