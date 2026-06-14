import { ImagePlus } from "lucide-react";
import type { ChangeEvent } from "react";

interface CoverDropzoneProps {
  cover: string | null;
  onCoverChange: (dataUrl: string) => void;
}

export function CoverDropzone({ cover, onCoverChange }: CoverDropzoneProps) {
  function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        onCoverChange(reader.result);
      }
    };
    reader.readAsDataURL(file);
  }

  return (
    <label className={cover ? "cover-dropzone has-cover" : "cover-dropzone"}>
      {cover ? (
        <img src={cover} alt="Selected idea cover" />
      ) : (
        <span className="cover-placeholder">
          <ImagePlus size={26} aria-hidden="true" />
          <strong>Add cover image</strong>
          <small>Attach a diagram, prompt card, or product preview.</small>
        </span>
      )}
      <span className="cover-upload">{cover ? "Replace cover image" : "Upload image"}</span>
      <input type="file" accept="image/*" onChange={handleFile} />
    </label>
  );
}
