import React, { useState } from "react";

import "./App.css";
import Results from "./components/Results";
import SearchBar from "./components/SearchBar";
import Summary from "./components/Summary";

function App() {
  const [results, setResults] = useState<Record<string, Array<string>>>({});

  return (
    <>
      <SearchBar onQueryProcessed={setResults} />
      <Results results={results} />
      <Summary />
    </>
  );
}

export default App;
