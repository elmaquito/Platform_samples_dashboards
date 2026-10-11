import { useState } from 'react';

export default function Slider({ slides }) {
  const [i, setI] = useState(0);
  const s = slides[i];
  return (
    <div className="rounded-lg border bg-white p-4 shadow">
      <h3 className="font-semibold mb-2">{s.title}</h3>
      <p className="mb-4 text-gray-700">{s.text}</p>
      <div className="flex gap-2">
        <button className="px-3 py-1 rounded bg-gray-200" onClick={() => setI((i - 1 + slides.length) % slides.length)}>←</button>
        <span className="self-center text-sm">{i + 1} / {slides.length}</span>
        <button className="px-3 py-1 rounded bg-gray-200" onClick={() => setI((i + 1) % slides.length)}>→</button>
      </div>
    </div>
  );
}
