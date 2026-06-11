import React, { useRef, useState } from "react";
import { uploadVideo } from "@/lib/api/feeds";

export default function AddVideo() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const onClick = () => {
    inputRef.current?.click();
  };

  const onChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setStatus("Uploading...");
    try {
      const res = await uploadVideo(file);
      setStatus(`Uploaded: ${res.feed_id}`);
    } catch (err: any) {
      setStatus(`Error: ${err.message}`);
    }
  };

  return (
    <div className="add-video">
      <input ref={inputRef} type="file" accept="video/*" onChange={onChange} style={{ display: "none" }} />
      <button onClick={onClick} className="btn btn-primary">Add Video</button>
      {status && <span style={{ marginLeft: 8 }}>{status}</span>}
    </div>
  );
}
