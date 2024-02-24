import { getRandomQuery } from "../utils/getRandomQuery";

export default function SearchBar() {
  return (
    <form>
      <input name="query" placeholder={"Search for " + getRandomQuery()}></input>
      <button>Search</button>
    </form>
  );
}
