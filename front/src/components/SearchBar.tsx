import { getRandomQuery } from "../utils/getRandomQuery";
import "./SearchBar.css";

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
      .then((data) => {
        console.log(data);
        onQueryProcessed(data);
      });
  };

  return (
    <div className="bar">
      <img
        src="https://preview.redd.it/w82j6chvnv131.png?width=1080&crop=smart&auto=webp&s=cdd336114b22bef9877b372064adb423f8101bdc"
        width={300}
      />
      <form onSubmit={handleSubmit} action="/api/process-query" method="post">
        <input
          name="query"
          size={100}
          placeholder={"Search for " + getRandomQuery()}
        ></input>
        <button>Search</button>
      </form>
    </div>
  );
}
