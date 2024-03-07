import { getRandomQuery } from "../utils/getRandomQuery";

interface SearchBarProps {
  onQueryProcessed: (docs: Record<string, Array<string>>) => void;
}

export default function SearchBar({ onQueryProcessed }: SearchBarProps) {
  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const form = event.currentTarget;
    const formData = new FormData(form);

    fetch(form.action, {
      method: form.method,
      body: formData,
    })
      .then((resp) => resp.json())
      .then((data) => onQueryProcessed(data));
  };

  return (
    <form onSubmit={handleSubmit} action="/api/process-query" method="post">
      <input
        name="query"
        placeholder={"Search for " + getRandomQuery()}
      ></input>
      <button>Search</button>
    </form>
  );
}
