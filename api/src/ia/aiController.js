import { generateResponse } from './aiService.js';

export const analyzeDocument = async (req, res) => {
  const { docContent, feedback } = req.body;
  
  try {
    const analysis = await generateResponse(`Analise o documento: ${docContent}. Feedback anterior: ${feedback}`);
    res.json({ analysis });
  } catch (error) {
    res.status(500).json({ message: 'Erro na análise IA', error });
  }
};
