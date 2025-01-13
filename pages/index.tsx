import axios from "axios";
import { useState } from "react";

export default function Home() {
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFiles(event.target.files);
    }
  };

  const handleUpload = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      alert("Por favor, selecione ao menos um arquivo.");
      return;
    }

    const formData = new FormData();
    Array.from(selectedFiles).forEach((file) => {
      formData.append("files", file);
    });

    try {
      const response = await axios.post("http://localhost:8000/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      if (response.data.download_url) {
        const downloadUrl = `http://localhost:8000${response.data.download_url}`;
        window.location.href = downloadUrl;
      } else {
        alert("Upload realizado, mas algo deu errado ao gerar o arquivo compactado.");
      }
    } catch (error) {
      console.error("Erro ao enviar os arquivos:", error);
      alert("Erro ao enviar os arquivos. Verifique o console para mais detalhes.");
    }
  };

  return (
    <div>
      <h1>Renomeador de NFs</h1>
      <input type="file" onChange={handleFileChange} multiple />
      <button onClick={handleUpload}>Enviar e Renomear</button>
    </div>
  );
}
