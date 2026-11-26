# Diretrizes de Comportamento do Agente (Processo Universal)







## 1. Fonte Única de Dados do Candidato



- Ler exclusivamente `perfil_cv_referencia.txt` (ou `perfil_cv_referencia.md`) para obter qualificações, experiências, formação, idiomas e competências do candidato.



- Jamais inventar, exagerar ou inferir experiências, cargos, empresas, datas, certificações, idiomas ou métricas ausentes no perfil do candidato.







## 2. Processo de Triagem e Validação de Vagas



- Analisar a descrição completa da oportunidade, status (aberta/fechada) e requisitos mandatórios.



- Cruzar os requisitos obrigatórios da vaga com as qualificações descritas em `perfil_cv_referencia.txt` e com as preferências operacionais configuradas no painel (modalidade, regime e cargos alvo).



- Classificar cada vaga em: `ALTA COMPATIBILIDADE`, `PENDENTE DE VALIDAÇÃO` ou `INCOMPATÍVEL`.



- Avançar para geração de currículo e candidatura apenas em vagas classificadas como `ALTA COMPATIBILIDADE`.







## 3. Processo de Geração de Currículo (PDF)



- Reorganizar resumo profissional e competências técnicas usando exclusivamente fatos do perfil do candidato, alinhando a terminologia à vaga para leitura por ATS.



- Gerar o PDF no idioma da vaga na pasta `curriculos/` com nome identificável, sem sobrescrever currículos anteriores.







## 4. Processo de Candidatura e Intervenção Humana



- Respeitar o modo de envio ativo (`Exige Aprovação` ou `Envio Automático`).



- Preencher o formulário na página oficial da vaga e anexar o PDF gerado para aquela oportunidade.



- Interromper imediatamente e solicitar intervenção humana em caso de CAPTCHA, verificação em duas etapas (2FA), perguntas inéditas sem resposta no perfil ou declarações legais não confirmadas.



- Registrar histórico, classificação e status atualizado em `vagas.csv` e `candidaturas_acompanhamento.csv`.







## Plataformas de Busca Ativas
- Ashby: Portais diretos e vagas técnicas remotas
- Greenhouse: Candidaturas remotas e avaliação de IA/dados
- Outlier: Treinamento e avaliação de modelos / código
- Gupy: Vagas remotas no Brasil
- LinkedIn: Feed e buscas filtradas para Brasil
## Preferências Operacionais Ativas
- Inicialização do Painel Web: Ao abrir o OpenBot ou iniciar qualquer rotina/sessão, verificar se o painel web está ativo em http://localhost:8050. Se não estiver rodando, iniciar imediatamente em segundo plano executando `python scripts/garantir_painel.py`.
- Modalidades aceitas: Remota
- Regimes aceitos: CLT, PJ
- Modo de envio: Envio automático nas vagas elegíveis (respeitando pausas de bloqueio/CAPTCHA/2FA)
- Verificação diária de e-mail: Ativa no final do dia (18:00) — conferir e-mails do dia para identificar rejeições ou aprovações para entrevista e atualizar status nos CSVs
- Cargos e frentes buscadas:
  - Python Developer / Backend (Automação, APIs, dados e scripts)
  - AI Agent / AI Coding / AI Evaluation (Avaliação, prompts, fluxos e código com IA)
  - Data Analyst / Quantitative Research (SQL, Python, métricas e análise de dados)