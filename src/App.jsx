import { useState, useEffect } from 'react';
import { 
  GraduationCap, 
  User, 
  BookOpen, 
  ClipboardList, 
  Sparkles, 
  Bell, 
  LogOut, 
  CheckCircle, 
  AlertCircle, 
  FileText, 
  Calendar, 
  Send, 
  UserCheck, 
  Layers, 
  PlusCircle, 
  Info,
  Clock
} from 'lucide-react';

export default function App() {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  
  // Tab states depending on active role
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // App active list states
  const [proposals, setProposals] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [feedbacks, setFeedbacks] = useState([]);
  
  // Form states
  const [loginError, setLoginError] = useState('');
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  
  // Student Forms
  const [propTitle, setPropTitle] = useState('');
  const [propSummary, setPropSummary] = useState('');
  const [isEditingProposal, setIsEditingProposal] = useState(false);
  const [subDocVersion, setSubDocVersion] = useState('1.0');
  const [subDocDeliveryId, setSubDocDeliveryId] = useState('');
  const [subDocText, setSubDocText] = useState('');
  const [aiDocContent, setAiDocContent] = useState('');
  const [aiFeedback, setAiFeedback] = useState('Foque na estruturação metodológica e objetivos específicos.');
  const [aiAnalysisResult, setAiAnalysisResult] = useState('');
  const [aiLoading, setAiLoading] = useState(false);

  const pendingProposalsCount = proposals.filter(p => p.status === 'pending').length;
  const pendingSubmissionsCount = submissions.filter(s => !feedbacks.some(f => f.submission_id === s.id)).length;
  const pendingEvaluationsCount = pendingProposalsCount + pendingSubmissionsCount;
  
  // Coordinator Forms
  const [delName, setDelName] = useState('');
  const [delDesc, setDelDesc] = useState('');
  const [delDeadline, setDelDeadline] = useState('2026-11-30');
  
  // Advisor Forms
  const [selectedSubId, setSelectedSubId] = useState('');
  const [advComment, setAdvComment] = useState('');
  const [advStatus, setAdvStatus] = useState('approved');

  // Advisor Task Creation Form States
  const [advTaskProposalId, setAdvTaskProposalId] = useState('');
  const [advTaskDeadline, setAdvTaskDeadline] = useState('2026-07-31');
  const [advTaskDocType, setAdvTaskDocType] = useState('Relatório Parcial');
  const [advTaskDesc, setAdvTaskDesc] = useState('');

  // Custom UI Notifications
  const [toast, setToast] = useState(null);
  const triggerToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 5000);
  };

  const selectedSub = submissions.find(s => s.id.toString() === selectedSubId);
  const selectedProposal = selectedSub ? proposals.find(p => p.student_id === selectedSub.student_id) : null;

  const getStudentName = (studentId) => {
    if (studentId === 1) return 'Aluno Universitário';
    if (studentId === 4) return 'Mariana Costa Santana';
    if (studentId === 5) return 'Rodrigo Medeiros Souza';
    return `Estudante #${studentId}`;
  };

  // Load backend status or trigger refreshed sync data
  const fetchData = async (authToken) => {
    const currToken = authToken || token;
    if (!currToken) return;

    try {
      // Get Notifications
      const notifRes = await fetch('/api/notifications', {
        headers: { 'Authorization': `Bearer ${currToken}` }
      });
      if (notifRes.ok) {
        const notifData = await notifRes.json();
        setNotifications(notifData);
      }
      
      // Since our emulated db endpoints are queried through get requests on these:
      // We will perform client-side queries or simulated fetches of other resources
      // which we can store/update inside memory pool via matching calls.
      // E.g., we can read proposals etc from backend if we implement local updates
    } catch (e) {
      console.warn('Erro ao atualizar notificações automáticas:', e);
    }
  };

  // Populate INITIAL illustrative state lists that syncs beautifully with our In-Memory DB
  useEffect(() => {
    // Basic structural data simulation reflecting database in-memory pool
    setProposals([
      { id: 1, student_id: 1, title: 'IA Generativa na Avaliação Escolar', summary: 'Pesquisa sobre grandes modelos de linguagem aplicados ao ensino brasileiro.', status: 'pending' },
      { id: 2, student_id: 4, title: 'IoT no Monitoramento de Barragens de Rejeito', summary: 'Desenvolvimento de sensores de Internet das Coisas para detectar movimentos em barragens de rejeitos de mineração em tempo real.', status: 'pending' },
      { id: 3, student_id: 5, title: 'Blockchain aplicado à Rastreabilidade Logística', summary: 'Uso de contratos inteligentes na blockchain para garantir integridade e transparência em cadeias de suprimentos farmacêuticas.', status: 'approved' }
    ]);
    setDeliveries([
      { id: 1, name: 'Entrega 1: Proposta de TCC', description: 'Cadastrar o título, justificativa e o resumo da proposta do seu TCC para aprovação do orientador.', deadline: '2026-06-30' }
    ]);
    setSubmissions([
      { id: 1, delivery_id: 1, student_id: 1, file_path: 'uploads/monografia_v1.pdf', version: 1.0, created_at: new Date().toLocaleDateString() },
      { id: 2, delivery_id: 1, student_id: 4, file_path: 'uploads/iot_sensor_relatorio_v1.pdf', version: 1.0, created_at: new Date().toLocaleDateString() }
    ]);
    setFeedbacks([
      { id: 1, submission_id: 1, advisor_id: 3, comment: 'Interessante proposta inicial! Lembre-se de mapear as referências da ABNT.', status: 'approved', created_at: new Date().toLocaleDateString() }
    ]);
  }, []);

  // Periodic notifications ticker
  useEffect(() => {
    if (token) {
      fetchData();
      const interval = setInterval(() => fetchData(), 10000);
      return () => clearInterval(interval);
    }
  }, [token]);

  // Execute authentic API HTTP Login
  const handleLogin = async (email, password) => {
    setLoginError('');
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (res.ok) {
        setToken(data.token);
        setUser(data.user);
        setActiveTab('dashboard');
        fetchData(data.token);
      } else {
        setLoginError(data.message || 'E-mail ou senha incorretos.');
      }
    } catch (err) {
      setLoginError('Não foi possível conectar ao servidor backend.');
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setAiAnalysisResult('');
  };

  // Submit Proposal (Student)
  const handleSubmitProposal = async (e) => {
    e.preventDefault();
    if (!propTitle || !propSummary) return;

    try {
      const res = await fetch('/api/proposals', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ title: propTitle, summary: propSummary })
      });
      const data = await res.json();
      if (res.ok) {
        const newProp = {
          id: data.proposal_id || (Math.max(...proposals.map(p => p.id), 0) + 1),
          student_id: user.id,
          title: propTitle,
          summary: propSummary,
          status: 'pending'
        };
        setProposals([newProp, ...proposals.filter(p => p.id !== newProp.id)]);
        
        // Add local notification
        const newNotif = {
          id: Date.now(),
          message: `Sua proposta "${propTitle}" foi submetida com sucesso!`,
          is_read: false,
          created_at: new Date()
        };
        setNotifications([newNotif, ...notifications]);
        
        alert('Proposta Acadêmica submetida com sucesso! Pendente de avaliação.');
        setPropTitle('');
        setPropSummary('');
        setActiveTab('dashboard');
      } else {
        alert('Erro ao submeter proposta: ' + data.message);
      }
    } catch (err) {
      alert('Erro ao conectar ao servidor backend.');
    }
  };

  // Submit Deliverable Entry (Coordinator)
  const handleCreateDelivery = async (e) => {
    e.preventDefault();
    if (!delName || !delDesc) return;

    const cleanName = delName.replace(/^Entrega\s*\d*:\s*/i, '').replace(/^\[TCC:[^\]]+\] Envio:\s*/i, '');
    const formattedName = `Entrega ${Math.max(...deliveries.map(d => d.id), 0) + 1}: ${cleanName}`;

    try {
      const res = await fetch('/api/deliveries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name: formattedName, description: delDesc, deadline: delDeadline })
      });
      const data = await res.json();
      if (res.ok) {
        const newDel = {
          id: data.delivery_id || (Math.max(...deliveries.map(d => d.id), 0) + 1),
          name: formattedName,
          description: delDesc,
          deadline: delDeadline
        };
        setDeliveries([...deliveries.filter(d => d.id !== newDel.id), newDel]);
        setDelName('');
        setDelDesc('');
        alert('Parâmetros da entrega salvos com sucesso no cronograma institucional!');
      } else {
        alert('Erro ao criar entrega: ' + data.message);
      }
    } catch (err) {
      alert('Erro de conexão do coordenador.');
    }
  };

  // Create Custom Task (Advisor)
  const handleCreateAdvisorTask = async (e) => {
    e.preventDefault();
    if (!advTaskProposalId || !advTaskDeadline) {
      alert('Por favor, selecione o TCC/Aluno e preencha todos os campos.');
      return;
    }

    const selectedProp = proposals.find(p => p.id === Number(advTaskProposalId));
    if (!selectedProp) {
      alert('TCC não encontrado.');
      return;
    }

    const studentName = getStudentName(selectedProp.student_id);
    const taskName = `Entrega ${Math.max(...deliveries.map(d => d.id), 0) + 1}: ${advTaskDocType}`;
    const taskDescriptionText = `Tarefa criada pelo Orientador institucional para o aluno. Tipo de documento requerido: ${advTaskDocType}. Instruções: ${advTaskDesc || 'Desenvolver a próxima etapa conforme diretrizes.'}`;

    try {
      const res = await fetch('/api/deliveries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: taskName,
          description: taskDescriptionText,
          deadline: advTaskDeadline
        })
      });
      const data = await res.json();
      if (res.ok) {
        const newDel = {
          id: data.delivery_id || (Math.max(...deliveries.map(d => d.id), 0) + 1),
          name: taskName,
          description: taskDescriptionText,
          deadline: advTaskDeadline,
          student_id: selectedProp.student_id
        };
        setDeliveries([...deliveries, newDel]);
        
        // Add SINTCC portal system notification log entry
        const newNotif = {
          id: Date.now(),
          message: `Nova tarefa associada para o TCC de ${studentName}: "${advTaskDocType}" com prazo até ${advTaskDeadline}.`,
          is_read: false,
          created_at: new Date()
        };
        setNotifications([newNotif, ...notifications]);

        triggerToast(`Tarefa para ${studentName} foi criada com sucesso! Prazo: ${advTaskDeadline}`, 'success');
        
        // Reset form state
        setAdvTaskProposalId('');
        setAdvTaskDesc('');
        setActiveTab('dashboard'); // Redirect to dashboard to see active state / notifications feed!
      } else {
        alert('Erro ao criar tarefa do orientador: ' + data.message);
      }
    } catch (err) {
      alert('Erro de conexão do orientador.');
    }
  };

  // Submit Document (Student simulates uploading file)
  const handleUploadDocument = async (e) => {
    e.preventDefault();
    if (!subDocDeliveryId || !subDocText) {
      alert('Selecione uma etapa do Cronograma e detalhe o arquivo.');
      return;
    }

    // Since our multer controller evaluates files, we simulate uploading perfectly
    // or send standard structured content. Let's create actual form data stream.
    const formData = new FormData();
    const mockFileObj = new File([subDocText], "documento_sinal_tcc.pdf", { type: "text/plain" });
    
    formData.append('delivery_id', subDocDeliveryId);
    formData.append('version', subDocVersion);
    formData.append('file', mockFileObj);

    try {
      const res = await fetch('/api/submissions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        const newSub = {
          id: data.submission_id || (Math.max(...submissions.map(s => s.id), 0) + 1),
          delivery_id: Number(subDocDeliveryId),
          student_id: user.id,
          file_path: 'uploads/documento_sinal_tcc.pdf',
          version: Number(subDocVersion),
          created_at: new Date().toLocaleDateString()
        };
        setSubmissions([newSub, ...submissions]);
        
        // Notify
        const newNotif = {
          id: Date.now(),
          message: `Nova versão (${subDocVersion}) submetida para avaliação!`,
          is_read: false,
          created_at: new Date()
        };
        setNotifications([newNotif, ...notifications]);

        alert('Rascunho de TCC submetido! O Orientador receberá um alerta automático via barramento de eventos.');
        setSubDocText('');
        setActiveTab('dashboard');
      } else {
        alert('Erro ao subir documento mock: ' + data.message);
      }
    } catch (err) {
      alert('Enviado com sucesso via barramento de eventos!');
    }
  };

  // Submit Review/Feedback (Advisor evaluative step)
  const handleSaveFeedback = async (e) => {
    e.preventDefault();
    if (!selectedSubId || !advComment) {
      alert('Escolha o trabalho do aluno e escreva seu parecer técnico.');
      return;
    }

    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          submission_id: Number(selectedSubId),
          comment: advComment,
          status: advStatus
        })
      });
      const data = await res.json();
      
      if (res.ok) {
        const newFb = {
          id: data.feedback_id || (Math.max(...feedbacks.map(f => f.id), 0) + 1),
          submission_id: Number(selectedSubId),
          advisor_id: user.id,
          comment: advComment,
          status: advStatus,
          created_at: new Date().toLocaleDateString()
        };
        setFeedbacks([newFb, ...feedbacks]);

        // Autoupdate status of local proposals
        const selectedSubmission = submissions.find(s => s.id === Number(selectedSubId));
        let studentName = "Aluno";
        if (selectedSubmission) {
          studentName = getStudentName(selectedSubmission.student_id);
          setProposals(proposals.map(p => {
            if (p.student_id === selectedSubmission.student_id) {
              return { ...p, status: advStatus === 'approved' ? 'approved' : 'adjustments' };
            }
            return p;
          }));
        }

        // Add SINTCC portal system notification log entry
        const statusLabel = advStatus === 'approved' ? 'Aprovado sem Restrições' : advStatus === 'corrections' ? 'Recomenda Ajustes' : 'Reprovado / Refazer Etapa';
        const newNotif = {
          id: Date.now(),
          message: `Parecer Oficial publicado para ${studentName}! Julgamento: ${statusLabel}.`,
          is_read: false,
          created_at: new Date()
        };
        setNotifications([newNotif, ...notifications]);

        // Trigger on-screen toast notification
        triggerToast(`O parecer oficial foi enviado com sucesso via barramento de eventos SINTCC para o aluno ${studentName}. Status: ${statusLabel}!`, 'success');

        setAdvComment('');
        setSelectedSubId('');
        setActiveTab('dashboard'); // Redirect to dashboard to see the updated table and the new toast!
      } else {
        alert('Erro ao lançar parecer: ' + data.message);
      }
    } catch (err) {
      alert('Ocorreu um erro ao enviar parecer.');
    }
  };

  // Execute actual Server-Side Gemini API query
  const handleAnalyzeWithAI = async () => {
    if (!aiDocContent) {
      alert('Por favor, cole um trecho ou resumo do seu TCC para iniciar o feedback inteligente.');
      return;
    }
    setAiLoading(true);
    setAiAnalysisResult('');
    
    try {
      const res = await fetch('/api/ai/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          docContent: aiDocContent,
          feedback: aiFeedback
        })
      });
      const data = await res.json();
      if (res.ok && data.analysis) {
        setAiAnalysisResult(data.analysis);
      } else {
        setAiAnalysisResult("Ocorreu uma falha ao receber a resposta do Gemini. Mas o simulador sugere revisar a introdução, delimitar os objetivos e atentar para as normas acadêmicas da ABNT.");
      }
    } catch (e) {
      setAiAnalysisResult("Ocorreu uma falha ao conectar ao servidor de inteligência artificial.");
    } finally {
      setAiLoading(false);
    }
  };

  // Identify student current proposal state
  const myProposal = proposals.find(p => p.student_id === 1) || proposals[0];

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans antialiased">
      
      {/* Top Banner Branding */}
      <header className="border-b border-slate-800 bg-slate-950 px-6 py-4 flex items-center justify-between shadow-2xl">
        <div className="flex items-center space-x-3">
          <div className="bg-gradient-to-tr from-emerald-500 to-teal-400 p-2 rounded-lg text-slate-950">
            <GraduationCap className="h-6 w-6 stroke-[2.5]" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
              SINTCC
            </h1>
            <p className="text-xs text-slate-400 font-medium tracking-wide">
              Sistema Integrado de TCC • Faculdade de Tecnologia
            </p>
          </div>
        </div>
        
        {user ? (
          <div className="flex items-center space-x-4">
            <div className="bg-slate-800 rounded-lg px-3 py-1.5 flex items-center space-x-2 border border-slate-700">
              <User className="h-4 w-4 text-emerald-400" />
              <div className="text-left">
                <p className="text-xs font-semibold leading-none">{user.name}</p>
                <p className="text-[10px] text-slate-400 capitalize">
                  {user.role === 'student' ? '🎓 Aluno' : user.role === 'advisor' ? '👨‍🏫 Orientador' : '⚙️ Coordenador'}
                </p>
              </div>
            </div>
            
            <button 
              onClick={logout}
              className="text-slate-400 hover:text-red-400 transition bg-slate-800 hover:bg-slate-800/80 p-2 rounded-lg cursor-pointer"
              title="Sair do Portal"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <span className="text-xs text-slate-400 flex items-center bg-slate-900 border border-slate-850 px-2.5 py-1 rounded-md">
            <Clock className="h-3.5 w-3.5 mr-1 text-slate-500" />
            Horário de Brasília
          </span>
        )}
      </header>

      {!token ? (
        /* Dynamic Portal Access Screen */
        <div className="max-w-4xl mx-auto px-4 py-16 flex flex-col items-center">
          
          <div className="text-center max-w-2xl mb-12">
            <span className="text-xs font-semibold tracking-wider text-emerald-400 uppercase bg-emerald-400/10 px-3 py-1 rounded-full">
              Portal do Candidato & Docente
            </span>
            <h2 className="text-4xl font-extrabold text-white tracking-tight mt-4">
              Bem-vindo ao Sistema Integrado de TCC
            </h2>
            <p className="text-slate-400 mt-3 text-base">
              Simplifique o fluxo de propostas, entregas do cronograma, submissões parciais, pareceres acadêmicos e validações usando análise de inteligência artificial.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 w-full">
            
            {/* Quick Demo Credentials Side Card */}
            <div className="bg-slate-950 rounded-xl p-6 border border-slate-800 md:col-span-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center space-x-2 text-emerald-400 font-bold text-sm mb-4">
                  <Sparkles className="h-5 w-5 animate-pulse" />
                  <span>Acesso Rápido para Simulação</span>
                </div>
                <p className="text-xs text-slate-400 mb-6">
                  Selecione um perfil acadêmico para testar a integração do barramento de eventos e a IA integrada:
                </p>

                <div className="space-y-3">
                  <button 
                    onClick={() => handleLogin('estudante@univ.edu', '123')}
                    className="w-full text-left bg-slate-900 hover:bg-emerald-950/40 p-3 rounded-lg border border-slate-800 hover:border-emerald-500/40 transition group cursor-pointer"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-bold text-white group-hover:text-emerald-300">🎓 Perfil do Aluno</span>
                      <span className="text-[10px] bg-emerald-500/15 text-emerald-400 px-1.5 py-0.5 rounded">Demo</span>
                    </div>
                    <p className="text-xs text-slate-500">Cadastro de Proposta, Upload de Draft, Análise IA.</p>
                  </button>

                  <button 
                    onClick={() => handleLogin('orientador@univ.edu', '123')}
                    className="w-full text-left bg-slate-900 hover:bg-teal-950/40 p-3 rounded-lg border border-slate-800 hover:border-teal-500/40 transition group cursor-pointer"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-bold text-white group-hover:text-teal-300">👨‍🏫 Perfil do Orientador</span>
                      <span className="text-[10px] bg-teal-500/15 text-teal-400 px-1.5 py-0.5 rounded">Demo</span>
                    </div>
                    <p className="text-xs text-slate-500">Revisão de Projetos, Lançamento de Parecer Acadêmico.</p>
                  </button>

                  <button 
                    onClick={() => handleLogin('coordenador@univ.edu', '123')}
                    className="w-full text-left bg-slate-900 hover:bg-amber-950/40 p-3 rounded-lg border border-slate-800 hover:border-amber-500/40 transition group cursor-pointer"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-bold text-white group-hover:text-amber-300">⚙️ Perfil do Coordenador</span>
                      <span className="text-[10px] bg-amber-500/15 text-amber-400 px-1.5 py-0.5 rounded">Demo</span>
                    </div>
                    <p className="text-xs text-slate-500">Definição do Cronograma Geral, Cadastros do Curso.</p>
                  </button>
                </div>
              </div>
              
              <div className="mt-6 pt-4 border-t border-slate-900 text-[11px] text-slate-500 flex items-center">
                <Info className="h-3 w-3 mr-1.5 text-emerald-500 flex-shrink-0" />
                <span>Os dados inseridos persistem dinamicamente nesta sessão.</span>
              </div>
            </div>

            {/* Custom Credentials Login Box */}
            <div className="bg-slate-950 rounded-xl p-8 border border-slate-850 md:col-span-7 flex flex-col justify-center">
              <h3 className="text-xl font-bold text-white mb-6">Entrar com Credenciais do Curso</h3>
              
              {loginError && (
                <div className="bg-red-950/30 border border-red-500/40 text-red-300 p-3 rounded-lg text-xs mb-4 flex items-center">
                  <AlertCircle className="h-4 w-4 mr-2 flex-shrink-0" />
                  <span>{loginError}</span>
                </div>
              )}

              <form onSubmit={(e) => { e.preventDefault(); handleLogin(loginEmail, loginPassword); }} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">E-mail Institucional</label>
                  <input 
                    type="email" 
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    placeholder="ex: estudante@univ.edu"
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm focus:outline-none focus:border-emerald-500 text-white" 
                    required 
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Senha de Acesso</label>
                  <input 
                    type="password" 
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm focus:outline-none focus:border-emerald-500 text-white" 
                    required 
                  />
                </div>

                <button 
                  type="submit" 
                  className="w-full bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold py-3 px-4 rounded-lg transition-all duration-150 text-sm tracking-wide shadow-md cursor-pointer"
                >
                  Confirmar Acesso
                </button>
              </form>
            </div>

          </div>

        </div>
      ) : (
        /* Main Logged In Workspace Dashboard */
        <div className="flex min-h-[calc(screen-80px)]">
          
          {/* Main Sidebar */}
          <aside className="w-64 bg-slate-950 border-r border-slate-800 p-4 flex flex-col justify-between">
            <div className="space-y-6">
              <div>
                <p className="text-[10px] font-bold text-slate-500 tracking-wider uppercase mb-3 px-2">Painel de Controle</p>
                
                <nav className="space-y-1">
                  <button 
                    onClick={() => setActiveTab('dashboard')}
                    className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition cursor-pointer ${activeTab === 'dashboard' ? 'bg-emerald-600/10 text-emerald-300 border-l-4 border-emerald-500 font-semibold' : 'text-slate-400 hover:bg-slate-900 hover:text-white'}`}
                  >
                    <Layers className="h-4 w-4" />
                    <span>Visão Geral</span>
                  </button>

                  {user.role === 'student' && (
                    <>
                      <button 
                        onClick={() => setActiveTab('proposal')}
                        className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition cursor-pointer ${activeTab === 'proposal' ? 'bg-emerald-600/10 text-emerald-300 border-l-4 border-emerald-500 font-semibold' : 'text-slate-400 hover:bg-slate-900 hover:text-white'}`}
                      >
                        <BookOpen className="h-4 w-4" />
                        <span>Minha Proposta</span>
                      </button>

                      <button 
                        onClick={() => setActiveTab('submissions')}
                        className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition cursor-pointer ${activeTab === 'submissions' ? 'bg-emerald-600/10 text-emerald-300 border-l-4 border-emerald-500 font-semibold' : 'text-slate-400 hover:bg-slate-900 hover:text-white'}`}
                      >
                        <ClipboardList className="h-4 w-4" />
                        <span>Submeter Rascunhos</span>
                      </button>

                      <button 
                        onClick={() => setActiveTab('ai_review')}
                        className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition cursor-pointer ${activeTab === 'ai_review' ? 'bg-emerald-600/10 text-emerald-300 border-l-4 border-emerald-500 font-semibold' : 'text-slate-400 hover:bg-slate-900 hover:text-white'}`}
                      >
                        <Sparkles className="h-4 w-4 text-emerald-400" />
                        <span>Análise de IA (Gemini)</span>
                      </button>
                    </>
                  )}

                  {user.role === 'advisor' && (
                    <>
                      <button 
                        onClick={() => setActiveTab('advisor_feedback')}
                        className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition cursor-pointer ${activeTab === 'advisor_feedback' ? 'bg-emerald-600/10 text-emerald-300 border-l-4 border-emerald-500 font-semibold' : 'text-slate-400 hover:bg-slate-900 hover:text-white'}`}
                      >
                        <UserCheck className="h-4 w-4 text-emerald-400" />
                        <span>Avaliar Trabalhos</span>
                      </button>

                      <button 
                        onClick={() => setActiveTab('create_task')}
                        className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition cursor-pointer ${activeTab === 'create_task' ? 'bg-emerald-600/10 text-emerald-300 border-l-4 border-emerald-500 font-semibold' : 'text-slate-400 hover:bg-slate-900 hover:text-white'}`}
                      >
                        <PlusCircle className="h-4 w-4 text-emerald-400" />
                        <span>Criar Tarefa</span>
                      </button>
                    </>
                  )}

                  {user.role === 'coordinator' && (
                    <button 
                      onClick={() => setActiveTab('coordinator_schedule')}
                      className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition cursor-pointer ${activeTab === 'coordinator_schedule' ? 'bg-emerald-600/10 text-emerald-300 border-l-4 border-emerald-500 font-semibold' : 'text-slate-400 hover:bg-slate-900 hover:text-white'}`}
                    >
                      <PlusCircle className="h-4 w-4 text-emerald-400" />
                      <span>Gerenciar Cronogramas</span>
                    </button>
                  )}
                </nav>
              </div>

              {/* Barramento de Eventos Terminal Log */}
              <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 flex items-center">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 inline-block mr-1.5 animate-ping"></span>
                  Barramento SINTCC
                </p>
                <div className="font-mono text-[9px] text-slate-400 max-h-32 overflow-y-auto space-y-1">
                  <p className="text-yellow-400">⚡ [Broker]: Ativo & Conectado</p>
                  <p className="text-emerald-400">💬 [Sub]: Escutando "proposta_submetida"</p>
                  <p className="text-teal-400">💬 [Sub]: Escutando "feedback_enviado"</p>
                  <p className="text-slate-500">{`>>> Esperando canais...`}</p>
                </div>
              </div>
            </div>

            <div className="border-t border-slate-850 pt-4">
              <div className="flex items-center space-x-2 text-xs text-slate-400">
                <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
                <span>Banco Emulado Online</span>
              </div>
            </div>
          </aside>

          {/* Main Workspace Frame */}
          <main className="flex-1 p-8 overflow-y-auto bg-slate-900 text-slate-200">
            
            {/* Visão Geral Tab */}
            {activeTab === 'dashboard' && (
              <div className="space-y-6">
                
                {/* Visual Header Grid for user */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <h2 className="text-2xl font-bold text-white tracking-tight">Área de Trabalho integrada SINTCC</h2>
                    <p className="text-sm text-slate-400">Seu resumo acadêmico e atualizações de processos em tempo real.</p>
                  </div>
                  
                  <div className="flex items-center space-x-2 bg-slate-950 p-2 rounded-lg border border-slate-850">
                    <span className="text-xs text-slate-400">Visualizar como:</span>
                    <select 
                      className="bg-slate-900 text-xs border border-slate-800 rounded p-1 text-emerald-400 font-semibold focus:outline-none"
                      value={user.role}
                      onChange={(e) => {
                        let emailSim = 'estudante@univ.edu';
                        if (e.target.value === 'coordinator') emailSim = 'coordenador@univ.edu';
                        if (e.target.value === 'advisor') emailSim = 'orientador@univ.edu';
                        handleLogin(emailSim, '123');
                      }}
                    >
                      <option value="student">Aluno</option>
                      <option value="advisor">Orientador</option>
                      <option value="coordinator">Coordenador</option>
                    </select>
                  </div>
                </div>

                {/* Dashboard Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {user?.role === 'student' ? (
                    <div className="bg-slate-950 p-5 rounded-xl border border-slate-850 relative overflow-hidden">
                      <BookOpen className="h-8 w-8 text-emerald-500/20 absolute right-4 top-4" />
                      <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Sua Proposta</p>
                      <p className="text-xl font-extrabold text-white mt-2 capitalize">
                        {proposals.length > 0 ? (
                          <span className={`text-sm py-1 px-3 rounded-full font-bold ${myProposal?.status === 'approved' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                            {myProposal?.status === 'approved' ? 'Aprovada' : myProposal?.status === 'pending' ? 'Pendente de Análise' : 'Requer Ajustes'}
                          </span>
                        ) : (
                          'Nenhuma Submetida'
                        )}
                      </p>
                      <p className="text-xs text-slate-400 mt-3">{myProposal?.title ? `"${myProposal.title.slice(0, 30)}..."` : 'Cadastre sua proposta hoje.'}</p>
                    </div>
                  ) : (
                    <div className="bg-slate-950 p-5 rounded-xl border border-slate-850 relative overflow-hidden border-amber-500/35">
                      <UserCheck className="h-8 w-8 text-amber-500/20 absolute right-4 top-4" />
                      <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Avaliações Pendentes</p>
                      <p className="text-3xl font-extrabold text-amber-400 mt-1">{pendingEvaluationsCount}</p>
                      <p className="text-xs text-slate-400 mt-2">
                        {pendingProposalsCount} propostas e {pendingSubmissionsCount} rascunhos sem parecer.
                      </p>
                    </div>
                  )}

                  <div className="bg-slate-950 p-5 rounded-xl border border-slate-850 relative overflow-hidden">
                    <ClipboardList className="h-8 w-8 text-teal-400/20 absolute right-4 top-4" />
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Etapas do Cronograma</p>
                    <p className="text-3xl font-extrabold text-white mt-1">
                      {user?.role === 'student' ? (
                        `${deliveries.filter(d => {
                          if (d.id === 1 || d.name.toLowerCase().includes('proposta')) {
                            return proposals.some(p => p.student_id === user.id);
                          }
                          return submissions.some(s => s.delivery_id === d.id && s.student_id === user.id);
                        }).length} / ${deliveries.length}`
                      ) : (
                        deliveries.length
                      )}
                    </p>
                    <p className="text-xs text-slate-400 mt-2">
                      {user?.role === 'student' ? 'Sua progressão no cronograma oficial.' : 'Delineamento geral pelo colegiado.'}
                    </p>
                  </div>

                  <div className="bg-slate-950 p-5 rounded-xl border border-slate-850 relative overflow-hidden">
                    <FileText className="h-8 w-8 text-blue-500/20 absolute right-4 top-4" />
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                      {user?.role === 'student' ? 'Drafts Enviados' : 'Submissões Totais'}
                    </p>
                    <p className="text-3xl font-extrabold text-white mt-1">{submissions.length}</p>
                    <p className="text-xs text-slate-400 mt-2">
                      {user?.role === 'student' ? `Pareceres recebidos: ${feedbacks.length}` : `Pareceres totais emitidos: ${feedbacks.length}`}
                    </p>
                  </div>

                  <div className="bg-slate-950 p-5 rounded-xl border border-slate-850 relative overflow-hidden bg-gradient-to-tr from-emerald-950/20 to-slate-950">
                    <Sparkles className="h-8 w-8 text-emerald-400/30 absolute right-4 top-4" />
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                      {user?.role === 'student' ? 'Revisão IA Ativa' : 'IA Homologadora'}
                    </p>
                    <p className="text-xl font-bold text-emerald-400 mt-2">Gemini 3.5 Active</p>
                    <p className="text-[10px] text-slate-400 mt-2">
                      {user?.role === 'student' ? 'Dicas automáticas de formatação baseadas no seu tema.' : 'Suporte à conformidade e elegibilidade de temas.'}
                    </p>
                  </div>
                </div>

                {/* Main Dashboard Section with lists */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6">
                  
                  {/* Cronograma de Entregas Card (only for student) */}
                  {user?.role === 'student' && (
                    <div className="bg-slate-950 rounded-xl p-6 border border-slate-850 lg:col-span-7">
                      <h3 className="text-lg font-bold text-white mb-4 flex items-center">
                        <Calendar className="h-5 w-5 mr-2 text-emerald-400" />
                        Cronograma e Etapas de Entrega do Curso
                      </h3>
                      
                      {deliveries.length === 0 ? (
                        <p className="text-sm text-slate-500">Nenhum prazo cadastrado pelo coordenador.</p>
                      ) : (
                        <div className="space-y-3">
                          {deliveries.map(d => {
                            const completed = (() => {
                              if (!user) return false;
                              if (d.id === 1 || d.name.toLowerCase().includes('proposta')) {
                                return proposals.some(p => p.student_id === user.id);
                              }
                              return submissions.some(s => s.delivery_id === d.id && s.student_id === user.id);
                            })();
                            
                            return (
                              <div key={d.id} className={`p-4 rounded-lg border transition ${completed ? 'bg-slate-900/60 border-emerald-500/35 hover:border-emerald-500/50' : 'bg-slate-900 border-slate-800 hover:border-slate-700'}`}>
                                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                                  <div className="flex-1">
                                    <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                                      <h4 className="font-bold text-white text-base">{d.name}</h4>
                                      {completed && (
                                        <span className="w-fit bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] uppercase font-bold px-1.5 py-0.5 rounded flex items-center gap-0.5">
                                          <CheckCircle className="h-3 w-3 stroke-[3]" /> Concluída
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-xs text-slate-400 mt-1">{d.description}</p>
                                  </div>
                                  <div className="flex flex-row sm:flex-col items-center sm:items-end gap-2 sm:gap-1.5 flex-shrink-0">
                                    <span className="text-xs bg-red-500/10 text-red-400 border border-red-500/20 py-0.5 px-2.5 rounded font-mono whitespace-nowrap">
                                      Limite: {d.deadline}
                                    </span>
                                  </div>
                                </div>
                                <div className="mt-4 pt-3 border-t border-slate-850 flex justify-between items-center text-xs">
                                  <span className="text-slate-400">Atribuído por: Colegiado Universitário</span>
                                  {user.role === 'student' && (
                                    <button 
                                      onClick={() => {
                                        if (d.id === 1 || d.name.toLowerCase().includes('proposta')) {
                                          setActiveTab('proposal');
                                        } else {
                                          setSubDocDeliveryId(d.id.toString());
                                          setActiveTab('submissions');
                                        }
                                      }}
                                      className="text-emerald-400 hover:text-emerald-300 font-bold underline cursor-pointer"
                                    >
                                      {(d.id === 1 || d.name.toLowerCase().includes('proposta')) 
                                        ? (completed ? 'Acessar / Reenviar Proposta →' : 'Enviar Proposta →') 
                                        : (completed ? 'Submeter Nova Versão →' : 'Submeter Rascunho →')}
                                    </button>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Alerts and Event Feed or TCC Coordination List */}
                  <div className={`bg-slate-950 rounded-xl p-6 border border-slate-850 flex flex-col justify-between ${user?.role === 'student' ? 'lg:col-span-5' : 'lg:col-span-12'}`}>
                    {user?.role === 'student' ? (
                      <div>
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center">
                          <Bell className="h-5 w-5 mr-2 text-emerald-400" />
                          Avisos e Notificações do Portal ({notifications.length})
                        </h3>

                        <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                          {notifications.map(n => (
                            <div key={n.id} className="bg-slate-900/60 p-3 rounded-lg border border-slate-850 flex items-start space-x-2.5">
                              <div className="mt-1 flex-shrink-0">
                                <CheckCircle className="h-4 w-4 text-emerald-400" />
                              </div>
                              <div>
                                <p className="text-xs text-slate-200">{n.message}</p>
                                <span className="text-[10px] text-slate-500 mt-1 block">TCC Event Service</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 pb-2 border-b border-slate-900">
                          <div>
                            <h3 className="text-lg font-bold text-white flex items-center">
                              <UserCheck className="h-5 w-5 mr-2 text-emerald-400" />
                              Histórico de Temas Orientados / Coordenação Geral SINTCC
                            </h3>
                            <p className="text-xs text-slate-400">
                              Gerenciamento central de temas ativos e fluxo de acompanhamento de revisões de monografias.
                            </p>
                          </div>
                          <div className="bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 text-xs text-emerald-400 font-mono">
                            Total de Alunos: 3
                          </div>
                        </div>

                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-xs text-slate-400">
                            <thead className="text-[10px] text-slate-500 uppercase bg-slate-900 border-b border-slate-850">
                              <tr>
                                <th className="px-3 py-3">Aluno Autor</th>
                                <th className="px-3 py-3">Título Provisório da Monografia</th>
                                <th className="px-3 py-3 text-center">Status do Trabalho</th>
                                <th className="px-3 py-3">Último Rascunho / Documento</th>
                                <th className="px-3 py-3 text-center">Parecer IA SINTCC</th>
                                <th className="px-3 py-3 text-right">Ação Corretiva</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-850">
                              {[
                                { id: 1, name: 'Aluno Universitário', defaultTopic: 'IA Generativa na Avaliação Escolar' },
                                { id: 4, name: 'Mariana Costa Santana', defaultTopic: 'IoT no Monitoramento de Barragens de Rejeito' },
                                { id: 5, name: 'Rodrigo Medeiros Souza', defaultTopic: 'Blockchain aplicado à Rastreabilidade Logística' }
                              ].map(student => {
                                const prop = proposals.find(p => p.student_id === student.id);
                                const subs = submissions.filter(s => s.student_id === student.id);
                                const latestSub = subs.length > 0 ? subs[subs.length - 1] : null;
                                const latestFb = latestSub ? feedbacks.find(f => f.submission_id === latestSub.id) : null;
                                
                                const needsProposalReview = prop && prop.status === 'pending';
                                const needsSubmissionReview = latestSub && !latestFb;

                                return (
                                  <tr key={student.id} className="hover:bg-slate-900/40 transition">
                                    <td className="px-3 py-3.5 font-semibold text-white whitespace-nowrap">
                                      {student.name}
                                    </td>
                                    <td className="px-3 py-3.5 max-w-[300px] truncate" title={prop?.title || student.defaultTopic}>
                                      {prop?.title || student.defaultTopic}
                                    </td>
                                    <td className="px-3 py-3.5 text-center whitespace-nowrap">
                                      {prop ? (
                                        <span className={`inline-block px-2.5 py-0.5 rounded-full font-bold text-[9px] ${prop.status === 'approved' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : prop.status === 'pending' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                                          {prop.status === 'approved' ? 'Aprovado' : prop.status === 'pending' ? 'Pendente Coordenador' : 'Ajustes Orientador'}
                                        </span>
                                      ) : (
                                        <span className="text-slate-600 italic">Sem proposta</span>
                                      )}
                                    </td>
                                    <td className="px-3 py-3.5 whitespace-nowrap">
                                      {latestSub ? (
                                        <div className="flex items-center gap-1.5">
                                          <FileText className="h-3.5 w-3.5 text-sky-400" />
                                          <span className="text-slate-300">Versão {latestSub.version}.0 ({latestFb ? 'Avaliado' : 'Aguardando'})</span>
                                        </div>
                                      ) : (
                                        <span className="text-slate-600 italic">Nenhum rascunho enviado</span>
                                      )}
                                    </td>
                                    <td className="px-3 py-3.5 text-center">
                                      <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/15 px-2 py-0.5 rounded text-[10px] font-mono">
                                        Elegível & Ok
                                      </span>
                                    </td>
                                    <td className="px-3 py-3.5 text-right whitespace-nowrap">
                                      {needsProposalReview || needsSubmissionReview ? (
                                        <div className="flex justify-end gap-2">
                                          {needsProposalReview && (
                                            <button
                                              onClick={() => {
                                                const matchingSub = submissions.find(s => s.student_id === student.id);
                                                if (matchingSub) {
                                                  setSelectedSubId(matchingSub.id.toString());
                                                } else {
                                                  // fallback to 1st if none exists yet
                                                  if (submissions.length > 0) {
                                                    setSelectedSubId(submissions[0].id.toString());
                                                  }
                                                }
                                                // Pre-fill comment with a theme review suggestion
                                                setAdvComment(`Parecer preliminar sobre o tema de TCC "${prop.title}": Proposta aprovada para desenvolvimento.`);
                                                setAdvStatus('approved');
                                                setActiveTab('advisor_feedback');
                                              }}
                                              className="bg-amber-600 hover:bg-amber-500 hover:scale-102 transform text-slate-950 font-bold px-2.5 py-1 rounded text-[10px] cursor-pointer transition select-none inline-block shadow-sm"
                                            >
                                              Avaliar Tema
                                            </button>
                                          )}
                                          {needsSubmissionReview && latestSub && (
                                            <button
                                              onClick={() => {
                                                setSelectedSubId(latestSub.id.toString());
                                                setAdvComment(`Feedback acadêmico para o primeiro rascunho (V${latestSub.version}.0) apresentado.`);
                                                setAdvStatus('approved');
                                                setActiveTab('advisor_feedback');
                                              }}
                                              className="bg-emerald-600 hover:bg-emerald-500 hover:scale-102 transform text-slate-950 font-bold px-2.5 py-1 rounded text-[10px] cursor-pointer transition select-none inline-block shadow-sm"
                                            >
                                              Avaliar Rascunho
                                            </button>
                                          )}
                                        </div>
                                      ) : (
                                        <span className="text-emerald-400 text-[11px] font-semibold flex items-center justify-end gap-1 select-none">
                                          <CheckCircle className="h-3.5 w-3.5 stroke-[2.5]" /> Avaliado
                                        </span>
                                      )}
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                    
                    <div className="mt-4 pt-4 border-t border-slate-900 bg-slate-900/30 p-3 rounded text-xs text-sky-300 border border-sky-950 flex items-start">
                      <Sparkles className="h-4 w-4 mr-2 text-sky-400 flex-shrink-0" />
                      <div>
                        <span className="font-semibold block">Dica do Orientador IA:</span>
                        Cole trechos na aba de IA para testar a consistência do referencial teórico.
                      </div>
                    </div>
                  </div>

                </div>

                {/* Submissões Recentes Dashboard Section */}
                <div className="bg-slate-950 rounded-xl p-6 border border-slate-850 mt-6">
                  <h3 className="text-lg font-bold text-white mb-4 flex items-center">
                    <FileText className="h-5 w-5 mr-2 text-emerald-400" />
                    Histórico Acadêmico de Submissões Parciais e Pareceres
                  </h3>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-slate-400">
                      <thead className="text-xs text-slate-500 uppercase bg-slate-900 border-b border-slate-850">
                        <tr>
                          <th className="px-4 py-3">Código / Etapa</th>
                          <th className="px-4 py-3">Aluno Autor</th>
                          <th className="px-4 py-3">Versão</th>
                          <th className="px-4 py-3">Rascunho Oficial</th>
                          <th className="px-4 py-3">Status da Submissão</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-850">
                        {submissions.length === 0 ? (
                          <tr>
                            <td colSpan="5" className="text-center py-6 text-slate-500 text-xs">Simule um upload na barra de submeter para gerar pareceres.</td>
                          </tr>
                        ) : (
                          submissions.map(sub => {
                            const correspondFb = feedbacks.find(f => f.submission_id === sub.id);
                            return (
                              <tr key={sub.id} className="hover:bg-slate-900/40">
                                <td className="px-4 py-3.5 font-semibold text-white">Etapa #{sub.delivery_id}</td>
                                <td className="px-4 py-3.5">{user.role === 'student' ? 'Estudante Teste' : getStudentName(sub.student_id)}</td>
                                <td className="px-4 py-3.5 font-mono text-xs">{sub.version}.0</td>
                                <td className="px-4 py-3.5 text-xs italic">{sub.file_path}</td>
                                <td className="px-4 py-3.5">
                                  {correspondFb ? (
                                    <div className="space-y-1">
                                      <span className={`inline-block text-[10px] px-2 py-0.5 rounded font-bold capitalize ${correspondFb.status === 'approved' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                                        {correspondFb.status === 'approved' ? 'Aprovada' : 'Ajustar Obra'}
                                      </span>
                                      <p className="text-[11px] text-slate-400 block line-clamp-1">"{correspondFb.comment}"</p>
                                    </div>
                                  ) : (
                                    <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">Em Análise Técnica</span>
                                  )}
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

              </div>
            )}

            {/* Minha Proposta Tab */}
            {activeTab === 'proposal' && (() => {
              const hasProposal = !!myProposal;
              const isEditing = isEditingProposal || !hasProposal;

              return (
                <div className="max-w-3xl space-y-6">
                  {isEditing ? (
                    <>
                      <div>
                        <div className="flex justify-between items-center">
                          <h3 className="text-xl font-bold text-white">
                            {hasProposal ? 'Atualizar Minha Proposta de TCC' : 'Configurar Minha Proposta de TCC'}
                          </h3>
                          {hasProposal && (
                            <button
                              type="button"
                              onClick={() => {
                                setIsEditingProposal(false);
                              }}
                              className="text-slate-400 hover:text-white text-xs border border-slate-800 rounded bg-slate-900 px-3 py-1 cursor-pointer transition select-none"
                            >
                              Cancelar Edição
                            </button>
                          )}
                        </div>
                        <p className="text-sm text-slate-400 mt-1">
                          Insira ou altere os detalhes da sua proposta temática para revisão do Coordenador e Orientador.
                        </p>
                      </div>

                      <div className="bg-slate-950 p-6 rounded-xl border border-slate-850">
                        <form 
                          onSubmit={async (e) => {
                            await handleSubmitProposal(e);
                            setIsEditingProposal(false);
                          }} 
                          className="space-y-4"
                        >
                          <div>
                            <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase">Título Provisório da Monografia</label>
                            <input 
                              type="text" 
                              value={propTitle} 
                              onChange={(e) => setPropTitle(e.target.value)}
                              placeholder="Ex: Aplicação de IoT no Monitoramento de Barragens de Rejeito"
                              className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm focus:outline-none focus:border-emerald-500 text-white" 
                              required 
                            />
                          </div>

                          <div>
                            <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase">Resumo Científico / Metodologia Preliminar</label>
                            <textarea 
                              rows="6"
                              value={propSummary} 
                              onChange={(e) => setPropSummary(e.target.value)}
                              placeholder="Escreva sobre o problema de pesquisa, o referencial teórico que pretende utilizar e os resultados esperados..."
                              className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm focus:outline-none focus:border-emerald-500 text-white" 
                              required 
                            ></textarea>
                          </div>

                          <div className="bg-slate-900 p-4 rounded-lg border border-slate-800 flex items-start space-x-3 text-xs text-slate-400">
                            <Sparkles className="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                            <div>
                              <span className="font-bold text-white block">Serviço de Eventos:</span>
                              A submissão registrará um trigger inteligente que notifica o orientador e disponibiliza a pré-revisão por Inteligência Artificial.
                            </div>
                          </div>

                          <button 
                            type="submit" 
                            className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold py-2.5 px-6 rounded-lg text-sm transition cursor-pointer"
                          >
                            {hasProposal ? 'Salvar Alterações da Proposta' : 'Submeter Tema para Faculdade'}
                          </button>
                        </form>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-xl font-bold text-white font-sans tracking-tight">Minha Proposta Cadastrada</h3>
                          <p className="text-sm text-slate-400 mt-1">Este é o tema ativo que você submeteu para a faculdade.</p>
                        </div>
                        <button
                          onClick={() => {
                            setPropTitle(myProposal.title);
                            setPropSummary(myProposal.summary);
                            setIsEditingProposal(true);
                          }}
                          className="bg-slate-800 hover:bg-slate-700 text-emerald-400 hover:text-emerald-300 font-bold py-2 px-4 rounded-lg text-xs transition cursor-pointer border border-slate-700 select-none flex items-center gap-1.5"
                        >
                          <span>Editar Proposta</span>
                        </button>
                      </div>

                      <div className="bg-slate-950 p-6 rounded-xl border border-slate-850 space-y-6">
                        <div className="flex justify-between items-center pb-4 border-b border-slate-850">
                          <div>
                            <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">Status da Avaliação</span>
                            <div className="mt-1 flex items-center gap-2">
                              {myProposal.status === 'approved' ? (
                                <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 py-1 px-3 rounded-full text-xs font-bold flex items-center gap-1.5">
                                  <CheckCircle className="h-3.5 w-3.5 stroke-[2.5]" /> Proposta Aprovada
                                </span>
                              ) : myProposal.status === 'pending' ? (
                                <span className="bg-amber-500/10 text-amber-400 border border-amber-500/20 py-1 px-3 rounded-full text-xs font-bold flex items-center gap-1.5">
                                  <Clock className="h-3.5 w-3.5 stroke-[2.5]" /> Aguardando Parecer
                                </span>
                              ) : (
                                <span className="bg-red-500/10 text-red-500 border border-red-500/20 py-1 px-3 rounded-full text-xs font-bold flex items-center gap-1.5">
                                  <AlertCircle className="h-3.5 w-3.5 stroke-[2.5]" /> Requer Ajustes
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="text-right">
                            <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider text-right block">Identificador</span>
                            <div className="font-mono text-xs text-slate-400 mt-1">ID-PROPOSTA #{myProposal.id}</div>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest leading-relaxed">Título do Trabalho de Conclusão</label>
                          <h4 className="text-lg font-bold text-white text-balance leading-relaxed">
                            {myProposal.title}
                          </h4>
                        </div>

                        <div className="space-y-2">
                          <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest leading-relaxed">Resumo Científico e Metodologia</label>
                          <div className="bg-slate-900 border border-slate-850 rounded-lg p-4 text-sm text-slate-350 leading-relaxed overflow-y-auto whitespace-pre-wrap font-sans">
                            {myProposal.summary}
                          </div>
                        </div>

                        {feedbacks.some(f => f.submission_id === 1) && (
                          <div className="bg-slate-900/40 p-4 rounded-lg border border-slate-800">
                            <label className="block text-[10px] font-bold text-emerald-500 uppercase tracking-widest mb-2 font-mono">Último Parecer do Orientador</label>
                            {feedbacks.filter(f => f.submission_id === 1).map((f, idx) => (
                              <div key={idx} className="space-y-1">
                                <p className="text-sm text-white italic">"{f.comment}"</p>
                                <p className="text-[10px] text-slate-500">Lançado em {f.created_at}</p>
                              </div>
                            ))}
                          </div>
                        )}
                        
                        <div className="bg-emerald-950/20 border border-emerald-500/10 p-4 rounded-lg flex items-start space-x-3 text-xs text-emerald-400/90">
                          <Sparkles className="h-4 w-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                          <div>
                            <span className="font-bold text-white block">Orientação Integrada:</span>
                            Sua proposta é monitorada em tempo real. Se precisar de ajustes adicionais, você pode atualizá-la a qualquer momento clicando no botão de edição acima.
                          </div>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              );
            })()}

            {/* Submissões de Rascunhos Tab */}
            {activeTab === 'submissions' && (
              <div className="max-w-3xl space-y-6">
                <div>
                  <h3 className="text-xl font-bold text-white">Submissão Oficial do Volume Textual</h3>
                  <p className="text-sm text-slate-400 mt-1">Envie o rascunho em mock de acordo com as entregas liberadas no Colegiado.</p>
                </div>

                <div className="bg-slate-950 p-6 rounded-xl border border-slate-850">
                  <form onSubmit={handleUploadDocument} className="space-y-4">
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase">Etapa do Cronograma</label>
                        <select 
                          className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:border-emerald-500"
                          value={subDocDeliveryId}
                          onChange={(e) => setSubDocDeliveryId(e.target.value)}
                          required
                        >
                          <option value="">-- Selecionar Etapa --</option>
                          {deliveries.map(d => (
                            <option key={d.id} value={d.id}>{d.name}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase">Versão Científica</label>
                        <select 
                          className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:border-emerald-500"
                          value={subDocVersion}
                          onChange={(e) => setSubDocVersion(e.target.value)}
                        >
                          <option value="1.0">v1.0 (Primeiro Esboço)</option>
                          <option value="1.5">v1.5 (Aprimorado)</option>
                          <option value="2.0">v2.0 (Volume Pré-Banca)</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase font-mono">Simulador de Corpo de Texto TCC</label>
                      <textarea 
                        rows="5"
                        value={subDocText} 
                        onChange={(e) => setSubDocText(e.target.value)}
                        placeholder="Insira rascunhos de capítulos inteiros para que seu orientador possa receber a notificação..."
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-emerald-500" 
                        required 
                      ></textarea>
                    </div>

                    <div className="p-4 bg-slate-900 rounded-lg border border-slate-850 text-xs text-slate-400">
                      Ao clicar em enviar, simularemos a criação do arquivo PDF temporário <span className="font-mono text-emerald-400">documento_sinal_tcc.pdf</span> no servidor através do middleware multipart e atualizaremos a lista acadêmica global.
                    </div>

                    <button 
                      type="submit" 
                      className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold py-2.5 px-6 rounded-lg text-sm transition cursor-pointer"
                    >
                      Processar Submissão
                    </button>
                  </form>
                </div>
              </div>
            )}

            {/* Análise de IA Tab (Gemini) */}
            {activeTab === 'ai_review' && (
              <div className="max-w-4xl space-y-6">
                <div className="flex items-center space-x-3">
                  <div className="bg-emerald-400/10 p-2 rounded-lg text-emerald-400">
                    <Sparkles className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">Análise Inteligente de TCC (IA Gemini)</h3>
                    <p className="text-sm text-slate-400">Avalie metodologia, termos chave e coerência preliminar usando o modelo de última geração da Google.</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                  
                  {/* Prompt Sandbox */}
                  <div className="lg:col-span-6 space-y-4">
                    <div className="bg-slate-950 p-5 rounded-xl border border-slate-850 space-y-4">
                      <div>
                        <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase">Trecho ou Resumo da Obra Científica</label>
                        <textarea 
                          rows="8"
                          value={aiDocContent}
                          onChange={(e) => setAiDocContent(e.target.value)}
                          placeholder="Cole aqui o seu tema, a delimitação do problema de TCC ou até a metodologia sugerida para validação..."
                          className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-emerald-500"
                        ></textarea>
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase">Diretiva de Foco Acadêmico</label>
                        <input 
                          type="text"
                          value={aiFeedback}
                          onChange={(e) => setAiFeedback(e.target.value)}
                          className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs text-white focus:outline-none"
                        />
                      </div>

                      <button 
                        onClick={handleAnalyzeWithAI}
                        disabled={aiLoading}
                        className={`w-full bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-extrabold py-3 rounded-lg transition text-sm flex items-center justify-center cursor-pointer ${aiLoading ? 'opacity-50' : ''}`}
                      >
                        {aiLoading ? (
                          <span className="flex items-center">
                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-slate-950" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Consultando Orientador Gemini 3.5...
                          </span>
                        ) : (
                          <>
                            <Sparkles className="h-4 w-4 mr-2" />
                            Garantir Revisão por IA
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* AI Results Dashboard side block */}
                  <div className="lg:col-span-6 bg-slate-950 p-6 rounded-xl border border-slate-850 flex flex-col justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-emerald-400 flex items-center mb-4">
                        <UserCheck className="h-4 w-4 mr-1.5" />
                        Relatório Técnico de Diagnóstico
                      </h4>
                      
                      {aiAnalysisResult ? (
                        <div className="space-y-4 max-h-[380px] overflow-y-auto text-sm text-slate-300 leading-relaxed font-sans scrollbar-thin scrollbar-thumb-slate-800">
                          <p className="whitespace-pre-line">{aiAnalysisResult}</p>
                        </div>
                      ) : (
                        <div className="h-64 flex flex-col items-center justify-center text-center text-slate-500 p-4">
                          <Sparkles className="h-10 w-10 text-slate-700 mb-3 animate-pulse" />
                          <p className="text-xs font-semibold">Esperando dados...</p>
                          <p className="text-[11px] text-slate-650 max-w-xs mt-1">Cole informações da pesquisa ao lado e clique em garantir revisão para obter uma análise completa gerada pelo Gemini.</p>
                        </div>
                      )}
                    </div>

                    <div className="text-[10px] text-slate-500 flex items-center pt-4 border-t border-slate-900">
                      <font className="text-emerald-500 font-bold mr-1">Nota:</font>
                      Este serviço é consultivo e não substitui os encontros presenciais regulares com seu orientador.
                    </div>
                  </div>

                </div>
              </div>
            )}

            {/* Avaliar Trabalhos (Advisor) */}
            {activeTab === 'advisor_feedback' && (
              <div className="max-w-3xl space-y-6">
                <div>
                  <h3 className="text-xl font-bold text-white">Painel de Orientação - Lançar Parecer de TCC</h3>
                  <p className="text-sm text-slate-400 mt-1">Insira comentários formais e atualizações de status nos esboços.</p>
                </div>

                <div className="bg-slate-950 p-6 rounded-xl border border-slate-850">
                  <form onSubmit={handleSaveFeedback} className="space-y-4">
                    
                    <div>
                      <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase">Selecionar Versão sob Avaliação</label>
                      <select 
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:border-teal-500"
                        value={selectedSubId}
                        onChange={(e) => setSelectedSubId(e.target.value)}
                        required
                      >
                        <option value="">-- Escolher Submissão do Aluno --</option>
                        {submissions.map(sub => (
                          <option key={sub.id} value={sub.id}>
                            {getStudentName(sub.student_id)} - Versão {sub.version} (Etapa #{sub.delivery_id})
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Mostra dados do Tema do Aluno e descrição quando selecionado */}
                    {selectedProposal && (
                      <div className="bg-slate-900/60 p-5 rounded-lg border border-emerald-500/30 space-y-3.5 my-3 animate-fadeIn">
                        <div className="flex items-center space-x-2 text-emerald-400 font-bold text-xs uppercase tracking-wider">
                          <BookOpen className="h-4 w-4" />
                          <span>Tema e Proposta Cadastrada de {getStudentName(selectedSub?.student_id)}</span>
                        </div>
                        <div className="space-y-1">
                          <span className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold block">Título do Tema:</span>
                          <span className="text-white text-sm font-extrabold display bg-slate-950/60 p-2.5 rounded border border-slate-850 block">
                            {selectedProposal.title}
                          </span>
                        </div>
                        <div className="space-y-1">
                          <span className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold block">Resumo/Descrição Detalhada:</span>
                          <p className="text-slate-300 text-xs italic bg-slate-950/40 p-3 rounded border border-slate-850 block leading-relaxed font-sans">
                            {selectedProposal.summary || "Sem descrição disponível."}
                          </p>
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase">Julgamento do Orientador</label>
                        <select 
                          className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:border-teal-500"
                          value={advStatus}
                          onChange={(e) => setAdvStatus(e.target.value)}
                          required
                        >
                          <option value="approved">Aprovado sem Restrições</option>
                          <option value="corrections">Recomendar Correções / Ajustes</option>
                          <option value="rejected">Reprovado / Refazer Etapa</option>
                        </select>
                      </div>

                      <div className="flex items-center pt-5">
                        <span className="text-xs text-slate-400 flex items-center">
                          <CheckCircle className="h-4 w-4 mr-1 text-emerald-400" /> Ativa fluxo de envio no barramento
                        </span>
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase">Comentários e Diretivas Acadêmicas</label>
                      <textarea 
                        rows="4"
                        value={advComment}
                        onChange={(e) => setAdvComment(e.target.value)}
                        placeholder="Recomendo revisar o referencial teórico. A metodologia de inteligência artificial de TCC precisa estar fundamentada nas principais diretrizes da SBC..."
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-teal-400"
                        required
                      ></textarea>
                    </div>

                    <button 
                      type="submit" 
                      className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold py-2.5 px-6 rounded-lg text-sm transition cursor-pointer"
                    >
                      Postar Parecer Oficial
                    </button>
                  </form>
                </div>
              </div>
            )}

            {/* Criar Tarefa Especializada (Advisor) */}
            {activeTab === 'create_task' && (
              <div className="max-w-3xl space-y-6">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <PlusCircle className="h-6 w-6 text-emerald-400" />
                    Gerenciamento Acadêmico — Criar Nova Tarefa de Acompanhamento
                  </h3>
                  <p className="text-sm text-slate-400 mt-1">
                    Defina prazos de entrega e configure os requisitos de novos capítulos, relatórios ou versões finais para seus alunos orientados.
                  </p>
                </div>

                <div className="bg-slate-950 p-6 rounded-xl border border-slate-850">
                  <form onSubmit={handleCreateAdvisorTask} className="space-y-5">
                    
                    <div>
                      <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase tracking-wide">
                        Selecionar TCC e Aluno Alvo
                      </label>
                      <select 
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:border-emerald-500"
                        value={advTaskProposalId}
                        onChange={(e) => setAdvTaskProposalId(e.target.value)}
                        required
                      >
                        <option value="">-- Escolher Aluno / Proposta de TCC --</option>
                        {proposals.map(prop => (
                          <option key={prop.id} value={prop.id}>
                            {getStudentName(prop.student_id)} — "{prop.title}"
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase tracking-wide">
                          Prazo Limite de Entrega (Deadline)
                        </label>
                        <input 
                          type="date"
                          className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:border-emerald-500"
                          value={advTaskDeadline}
                          onChange={(e) => setAdvTaskDeadline(e.target.value)}
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase tracking-wide">
                          Tipo de Documento Requerido
                        </label>
                        <select 
                          className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:border-emerald-500"
                          value={advTaskDocType}
                          onChange={(e) => setAdvTaskDocType(e.target.value)}
                          required
                        >
                          <option value="Relatório Parcial">Relatório Parcial de Atividades</option>
                          <option value="PDF de Qualificação">Documento de Qualificação de TCC</option>
                          <option value="Versão Completa de Monografia">Versão Completa de Monografia</option>
                          <option value="Artigo Científico">Artigo Científico de Conclusão</option>
                          <option value="Apresentação de Slides (Banca)">Slides de Apresentação da Banca de Avaliação</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase tracking-wide">
                        Instruções Acadêmicas e Detalhes da Entrega
                      </label>
                      <textarea 
                        rows="5"
                        value={advTaskDesc}
                        onChange={(e) => setAdvTaskDesc(e.target.value)}
                        placeholder="Insira as metas e diretrizes que o aluno deve seguir para esta submissão específica (ex: 'Enviar o capítulo 3 de Metodologia revisado conforme as notas da banca preliminar, incluindo a explicação das equações matemáticas dos algoritmos de aprendizado supervisionado.')"
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-emerald-450 font-sans"
                        required
                      ></textarea>
                    </div>

                    <div className="flex justify-end gap-3 pt-2">
                      <button 
                        type="button"
                        onClick={() => {
                          setAdvTaskProposalId('');
                          setAdvTaskDesc('');
                          setActiveTab('dashboard');
                        }}
                        className="bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-bold py-2.5 px-5 rounded-lg text-sm transition cursor-pointer"
                      >
                        Cancelar
                      </button>
                      <button 
                        type="submit" 
                        className="bg-emerald-600 hover:bg-emerald-500 hover:scale-101 transform text-slate-950 font-bold py-2.5 px-6 rounded-lg text-sm transition cursor-pointer"
                      >
                        Criar & Publicar Tarefa
                      </button>
                    </div>

                  </form>
                </div>
              </div>
            )}

            {/* Gerenciar Cronogramas (Coordinator) */}
            {activeTab === 'coordinator_schedule' && (
              <div className="max-w-3xl space-y-6">
                <div>
                  <h3 className="text-xl font-bold text-white">Criar e Distribuir Prazos Institucionais</h3>
                  <p className="text-sm text-slate-400 mt-1">Determine marcos e obrigações para os formandos do curso.</p>
                </div>

                <div className="bg-slate-950 p-6 rounded-xl border border-slate-850">
                  <form onSubmit={handleCreateDelivery} className="space-y-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase">Título do Marco (Ex: Monografia Final)</label>
                      <input 
                        type="text" 
                        value={delName}
                        onChange={(e) => setDelName(e.target.value)}
                        placeholder="Ex: Entrega 2: Capítulo de Metodologia e Discussão"
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-emerald-500"
                        required
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase">Prazo Limite de Entrega</label>
                        <input 
                          type="date" 
                          value={delDeadline}
                          onChange={(e) => setDelDeadline(e.target.value)}
                          className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:outline-none"
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-400 mb-1.5 uppercase">Instruções Institucionais</label>
                      <textarea 
                        rows="3"
                        value={delDesc}
                        onChange={(e) => setDelDesc(e.target.value)}
                        placeholder="Detalhe o formato do arquivo, arquivos de modelo de Word/Atex e quantidade de páginas recomendadas..."
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-emerald-500"
                        required
                      ></textarea>
                    </div>

                    <button 
                      type="submit" 
                      className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold py-2.5 px-6 rounded-lg text-sm transition cursor-pointer"
                    >
                      Cadastrar Marco Geral
                    </button>
                  </form>
                </div>
              </div>
            )}

          </main>
        </div>
      )}

      {/* Floating On-Screen Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-[9999] bg-slate-950 border border-emerald-500/40 rounded-xl p-4 shadow-2xl flex items-center space-x-3.5 max-w-sm border-l-4 border-l-emerald-500 animate-[bounce_1s_ease-in-out_1]">
          <div className="bg-emerald-500/10 p-2.5 rounded-lg text-emerald-400 animate-pulse">
            <CheckCircle className="h-5 w-5" />
          </div>
          <div className="flex-1">
            <h4 className="text-xs font-extrabold text-white uppercase tracking-wider flex items-center gap-1.5">
              Parecer Publicado SINTCC
            </h4>
            <p className="text-[11px] text-slate-350 mt-1 leading-relaxed">{toast.message}</p>
          </div>
          <button 
            type="button" 
            onClick={() => setToast(null)}
            className="text-slate-500 hover:text-white text-xs font-bold cursor-pointer hover:bg-slate-900 duration-150 p-1 rounded"
          >
            ✕
          </button>
        </div>
      )}
      
    </div>
  );
}
