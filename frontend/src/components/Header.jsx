import logo from "../assets/logo.svg";

export default function Header() {
  return (
    <header className="w-full animate-rise border border-white/10 bg-ink-900/75 p-5 px-10 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <img src={logo} alt="Cassandra logo" className="h-10 w-10" />
      </div>
    </header>
  );
}
