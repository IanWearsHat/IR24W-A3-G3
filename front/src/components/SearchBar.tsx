import { getRandomQuery } from "../utils/getRandomQuery";

export default function SearchBar() {
  return (
    <form action="/api/process-query" method="post">
      <input
        name="query"
        placeholder={"Search for " + getRandomQuery()}
      ></input>
      <button>Search</button>
    </form>
  );
}
