import { GoogleGenAI } from '@google/genai';

const ai = new GoogleGenAI({
  apiKey: process.env.GEMINI_API_KEY,
  httpOptions: {
    headers: {
      'User-Agent': 'aistudio-build',
    }
  }
});

export const generateResponse = async (prompt) => {
  if (!process.env.GEMINI_API_KEY) {
    return "A chave do Gemini não foi encontrada no ambiente. Configure as Secrets se necessário. Resposta simulada: O documento contém uma estrutura inicial válida de TCC, porém recomenda-se aprofundar a fundamentação teórica.";
  }
  
  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3.5-flash',
      contents: prompt,
      config: {
        systemInstruction: "Você é um experiente orientador acadêmico brasileiro. Ajude a avaliar propostas e revisar documentos de TCC com críticas construtivas e sugestões práticas de aprimoramento em português brasileiro.",
      }
    });
    return response.text;
  } catch (err) {
    console.error('Erro na chamada ao Gemini:', err);
    return "Erro de conexão com o Gemini API. Sugerimos verificar o conteúdo do documento e tentar novamente.";
  }
};

