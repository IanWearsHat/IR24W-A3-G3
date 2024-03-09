import React, { useState } from "react";

import "./App.css";
import Results from "./components/Results";
import SearchBar from "./components/SearchBar";
import Summary from "./components/Summary";

function App() {
  const [results, setResults] = useState<Record<string, Array<string>>>({});

  return (
    <>
      {/* no need to consider the rendering on the part of the user if you create a
      web GUI - from last slide of Lecture 14 */}
      <SearchBar onQueryProcessed={setResults} />
      <Results results={results} />
      {/* <Summary /> */}
    </>
  );
}

export default App;
