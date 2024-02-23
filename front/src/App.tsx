import "./App.css";
import Results from "./components/Results";
import SearchBar from "./components/SearchBar";
import Summary from "./components/Summary";

function App() {
  // function handleClick() {
  //   fetch("/api/hello")
  //   .then((response) => response.text())
  //   .then((data) => console.log(data));
  // }

  return (
    <>
      <SearchBar />
      <Results />
      <Summary />
    </>
  );
}

export default App;
