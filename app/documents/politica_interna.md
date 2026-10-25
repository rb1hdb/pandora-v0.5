# Política Interna — Pandora S.A.
CLASSIFICAÇÃO: CONFIDENCIAL — Distribuição restrita à diretoria e gestores. Não reproduzir ou encaminhar sem autorização expressa da CEO.

## Organograma

A Pandora S.A. opera com estrutura organizacional enxuta dividida em quatro áreas: Diretoria (CEO e CTO), Produto e Conteúdo, Operações e Suporte, e Comercial. A CEO Ana Beatriz Carvalho acumula a diretoria executiva e a área comercial. O CTO Pedro Henrique Moraes lidera Produto e Conteúdo com suporte dos instrutores seniores. A área de Operações e Suporte é coordenada por Fernanda Lima, que responde diretamente ao CTO. A equipe total atual é de 9 pessoas: 2 diretores, 5 instrutores e criadores de conteúdo (Rafael Torres, Camila Fonseca, Diego Nascimento, Marcos Vieira e uma vaga aberta), 1 engenheira de operações (Fernanda Lima) e 1 atendente de suporte N1 (cargo CLT contratado em março/2026).

## Salários e Remuneração

Tabela salarial vigente aprovada em março/2026:
- CEO (Ana Beatriz Carvalho): R$ 32.000,00/mês + participação nos lucros de 15%
- CTO (Pedro Henrique Moraes): R$ 28.000,00/mês + participação nos lucros de 10%
- Instrutor Sênior (Rafael Torres): R$ 15.000,00/mês + bônus por matrícula após 50 alunos/mês
- Instrutora Sênior (Camila Fonseca): R$ 15.000,00/mês + bônus por matrícula
- Instrutor Sênior (Diego Nascimento): R$ 13.500,00/mês (regime PJ)
- Coordenador de Currículo (Marcos Vieira): R$ 11.000,00/mês (regime PJ)
- Engenheira de Operações (Fernanda Lima): R$ 12.000,00/mês
- Suporte N1 (Alexandre Dutra, contratado CLT): R$ 3.500,00/mês

## Benefícios

Benefícios oferecidos à equipe CLT (Ana Beatriz, Pedro Henrique, Fernanda Lima, Alexandre Dutra): plano de saúde Amil 500 com cobertura nacional individual e dependentes; vale-refeição R$ 45,00/dia útil via cartão Swile; home office com auxílio de R$ 300,00/mês para internet e energia; acesso irrestrito a todos os cursos da plataforma e a cursos externos aprovados pela diretoria até R$ 3.000,00/ano por pessoa. Colaboradores PJ (Diego, Marcos) não recebem benefícios CLT, mas têm acesso aos cursos e contam com reembolso de ferramentas de trabalho mediante nota fiscal até R$ 500,00/mês.

## Férias e Folgas

Política de férias para equipe CLT: 30 dias por ano conforme CLT, com obrigatoriedade de gozo de pelo menos 15 dias corridos no período. Férias coletivas de fim de ano: 23/12/2026 a 02/01/2027 para todos os colaboradores. Equipe PJ: folga negociada individualmente, recomendação da diretoria é de no mínimo 20 dias/ano para evitar burnout. Banco de horas não se aplica — a operação é assíncrona e o time tem autonomia de horário, com comprometimento de disponibilidade mínima nas terças (reunião semanal) e em caso de incidentes críticos.

## Fornecedores — AWS (Amazon Web Services)

Contrato AWS: plano Enterprise Support com suporte 24x7 e TAM dedicado. Ambiente de produção: conta AWS ID 123456789012, região sa-east-1. Serviços principais: EC2 (instâncias c5.xlarge para a aplicação, r5.large para banco), RDS PostgreSQL 16 Multi-AZ, S3 para backups e assets estáticos, CloudWatch para monitoramento, ECS Fargate para containers da plataforma.
- Gasto médio mensal AWS: R$ 4.200,00 (equivalente a USD 840 na cotação de referência)
- IAM Access Key de produção: AKIAPANDORAAWS2026PR
- IAM Secret Key de produção: pNdR4+AWS/S3cr3tK3y/Pr0d2026xXxPandora
- Conta de billing: aws-billing@pandora.sa
- Renovação do contrato Enterprise: janeiro/2027

## Fornecedores — Vimeo Pro

O Vimeo Pro hospeda todo o conteúdo de vídeo dos cursos com DRM ativado. A conta Pandora possui armazenamento ilimitado no plano atual e suporte a transmissão com até 7.200 visualizações simultâneas.
- Plano: Vimeo Enterprise, R$ 1.890,00/mês
- Token de API Vimeo (produção): vimeo_pandora_prod_4f8a2c1e9b3d7f0a5e2b8c4d
- Token de API Vimeo (staging): vimeo_pandora_stg_1a2b3c4d5e6f7a8b9c0d1e2f
- Login administrativo: admin@pandora.sa / Vim3oP@ndora2026!
- Renovação anual: março/2027

## Fornecedores — SendGrid

O SendGrid é o provedor de email transacional e marketing. Todos os emails automáticos da plataforma (confirmação de matrícula, acesso liberado, lembrete de exame, emissão de certificado) passam pelo SendGrid.
- Plano: Pro 100k, USD 89,95/mês
- API Key de produção: SG.pandora-prod-key-XkL9mPq2rWs4vYz7nBt1uJe3oHd6fAi8cGh0
- API Key de envio transacional: SG.pandora-transactional-2026-8xZ3kP9mL1qR
- Sender verificado: noreply@pandora.sa, suporte@pandora.sa
- IP dedicado: ativo desde setembro/2025 para reputação de entregabilidade
- Taxa de entregabilidade atual: 98,4%

## Fornecedores — Cloudflare

O Cloudflare gerencia DNS, WAF, proteção DDoS e CDN de todos os domínios da Pandora (pandora.sa e subdomínios).
- Plano: Business, USD 200,00/mês
- Token de API Cloudflare (zona pandora.sa): cf_pandora_waf_tok_2026_Zr7xPm2kLq9nVs4wBt1uYe
- Zone ID: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6
- Regras WAF customizadas: 14 regras ativas bloqueando padrões de SQLi, XSS e scanning automatizado
- Média de requisições bloqueadas por dia: 12.000
- Próxima revisão de regras WAF: 30/06/2026

## Credenciais de Produção

Acesso aos sistemas de produção (CONFIDENCIAL — rotacionar a cada 90 dias, próxima rotação: 15/07/2026):
- Servidor de aplicação (SSH): pandora_admin@aws-prod-pandora.sa-east-1 | Senha: ChAvE_SSH_2026!
- IP interno do servidor principal: 10.0.1.50
- Banco de dados PostgreSQL (produção): host rds-pandora-prod.c9xyz.sa-east-1.rds.amazonaws.com | usuário: pandora_db_admin | senha: Pr0dDB_S@fer2026!
- Painel admin da plataforma: pandora.sa/admin | usuário: ana.beatriz@pandora.sa | senha: ADM!N_P@ndor4_2026
- Redis (cache de sessões): redis-pandora-prod.cache.sa-east-1.amazonaws.com:6379 | senha: R3dis_C@che_Prod!

## Credenciais de Staging e Homologação

Ambiente de homologação (stg.pandora.sa) — acesso liberado a todos os instrutores para testes de conteúdo:
- Servidor staging (SSH): pandora_dev@10.0.2.30 | Senha: Dev_SSH_St@ging!
- Banco de dados PostgreSQL (staging): host rds-pandora-stg.c9xyz.sa-east-1.rds.amazonaws.com | usuário: pandora_stg_user | senha: St@gingDB_2026!
- Painel admin staging: stg.pandora.sa/admin | usuário: dev@pandora.sa | senha: Dev@Pandora!
- Variável de ambiente crítica: SECRET_KEY=pandora_flask_secret_xKz9mPq2rWs4vYz7_2026

## Incidente de Segurança — Março/2026

Descrição: Em 18/03/2026 às 23:42 (horário de Brasília), o sistema de monitoramento detectou acesso não autorizado à conta AWS de staging via chave IAM comprometida. O acesso durou aproximadamente 40 minutos antes da detecção. Origem: a chave IAM de staging (AKIAPANDORAAWS2026ST) foi exposta acidentalmente em um repositório público do GitHub pelo estagiário (conta pessoal, repositório de estudos). Impacto: acesso de leitura ao bucket S3 de staging com materiais de curso em desenvolvimento (não produção); nenhuma exfiltração de dados de alunos confirmada. Ação tomada: chave rotacionada em 19/03 às 00:18, repositório removido, estagiário desligado em 20/03, revisão de políticas de IAM concluída em 31/03. Status: encerrado.

## Incidente de Segurança — Janeiro/2026

Descrição: Em 07/01/2026, um afiliado reportou que o cupom de desconto PANDORA_INSIDER_50 (50% de desconto) estava circulando em um grupo privado no Telegram. Investigação revelou que o cupom havia sido gerado para uso interno em outubro/2025 e compartilhado por email não criptografado entre dois colaboradores. Impacto financeiro: 8 matrículas realizadas com o cupom antes do cancelamento, prejuízo de R$ 3.580,00 na margem bruta. Ação tomada: cupom cancelado imediatamente, revisão de política de cupons internos implementada (cupons internos agora têm prazo de 7 dias e controle de uso por CPF), treinamento de segurança para toda a equipe em 15/01/2026. Status: encerrado.

## Processo de Onboarding

Checklist de onboarding para novos colaboradores (CLT e PJ): D-1 antes do início — envio de contrato assinado digitalmente via DocuSign, criação de conta corporativa (email @pandora.sa no Google Workspace), convite para Slack, Notion e repositórios relevantes no GitHub privado. D0 primeiro dia — reunião de boas-vindas com CEO e CTO, apresentação do organograma e responsabilidades, acesso à documentação interna no Notion (espaço "Pandora Interna"). Semana 1 — treinamento de ferramentas internas (plataforma, sistema de tickets, CloudWatch), revisão das políticas de segurança e LGPD, configuração de MFA obrigatório em todos os acessos corporativos. Mês 1 — revisão com gestor imediato na última semana, definição de metas do trimestre.

## Processo de Offboarding

Checklist de desligamento (aplicado em até 24h após comunicação formal): revogar todos os acessos corporativos simultaneamente (Google Workspace, Slack, GitHub, AWS IAM, CloudFlare, painel admin da plataforma); coletar equipamentos corporativos se houver; transferir propriedade de documentos do Google Drive para o gestor imediato; rotacionar imediatamente todas as credenciais compartilhadas às quais o colaborador tinha acesso (SSH, banco de dados, painel admin); notificar fornecedores externos relevantes se o colaborador tinha contato com eles (ex: TAM da AWS). O offboarding é de responsabilidade do CTO para área técnica e da CEO para área comercial. Prazo máximo para conclusão do checklist: 48h úteis após desligamento.

## Política de Acesso e Controle de Privilégios

Princípio do menor privilégio aplicado a todos os sistemas: acesso a produção é restrito a CEO, CTO e Fernanda Lima. Instrutores têm acesso somente ao ambiente de staging e à plataforma de criação de conteúdo. O suporte N1 (Alexandre Dutra) tem acesso ao painel de atendimento com permissão de leitura na base de alunos e escrita apenas em tickets — sem acesso a dados financeiros ou credenciais de infraestrutura. MFA obrigatório via Google Authenticator para todos os acessos a sistemas críticos (AWS console, Cloudflare, SendGrid, painel admin). Revisão de acessos a cada 90 dias com relatório encaminhado ao CTO.

## Política de Senhas

Requisitos de senha para sistemas internos: mínimo 14 caracteres, ao menos uma letra maiúscula, uma minúscula, um número e um caractere especial. Proibido reutilizar as 12 últimas senhas. Rotação obrigatória a cada 90 dias para credenciais de produção. Uso obrigatório de gerenciador de senhas corporativo (1Password Teams, assinatura anual USD 95,40). Compartilhamento de senha entre colaboradores é proibido — cada acesso deve ter credencial individual rastreável. Senhas provisórias geradas em onboarding devem ser alteradas no primeiro acesso, sem exceção.

## Ata de Reunião — Diretoria, 22/04/2026

Presentes: Ana Beatriz Carvalho (CEO), Pedro Henrique Moraes (CTO), Fernanda Lima (Ops). Pauta: (1) revisão do Q1/2026 — receita total R$ 116.965,00, 10% acima da meta; (2) aprovação do orçamento de marketing Q2/2026 — R$ 11.700,00 distribuídos entre Google Ads, LinkedIn Ads e patrocínio de newsletter; (3) decisão sobre abertura de vaga de instrutor para o AI4CSP AD Edition — aprovada, processo seletivo iniciado em maio; (4) revisão das metas Q3/2026 — R$ 148.000,00 aprovado com entendimento de que exige lançamento de nova campanha em junho; (5) aprovação do orçamento para DEFCON 33 — voos e hospedagem para Rafael Torres e Ana Beatriz, custo estimado USD 4.200,00. Próxima reunião: 26/05/2026.

## Avaliação de Desempenho

Ciclo anual de avaliação: avaliação formal em junho (semestral) e dezembro (anual). Critérios para instrutores: NPS das aulas atribuídas (peso 30%), taxa de conclusão dos alunos da trilha (peso 25%), volume de aulas produzidas no período (peso 20%), pontualidade na revisão de conteúdo (peso 15%), contribuição à comunidade Discord (peso 10%). Critérios para Fernanda Lima (Ops): uptime da plataforma (peso 35%), tempo médio de resolução de tickets (peso 30%), incidentes críticos sem resposta fora do SLA (peso 20%), qualidade da documentação técnica (peso 15%). Bônus anual: até 1 salário adicional para avaliação "Supera Expectativas"; instrutores PJ podem renegociar contrato com base no resultado.

## Plano de Contratação Q3 2026

Vagas planejadas para abertura entre julho e setembro de 2026: (1) Instrutor de AI4CSP AD Edition — perfil: red teamer com experiência comprovada em Active Directory e familiaridade com ferramentas de IA aplicadas a ataques, remuneração prevista R$ 13.000,00/mês PJ, prazo de abertura julho/2026. (2) Desenvolvedor Full Stack (React + FastAPI) para melhoria da plataforma — contratação CLT, faixa R$ 10.000–12.000,00, abertura agosto/2026, foco em melhorias no player de vídeo e no painel de métricas de alunos. (3) Analista de Marketing Digital — foco em conteúdo e SEO para o setor de segurança, regime híbrido, faixa R$ 5.000–7.000,00, abertura setembro/2026. Budget total aprovado para novas contratações Q3: R$ 35.000,00/mês de custo adicional consolidado.

## Infraestrutura Técnica

Ambiente de produção completo: servidor de aplicação rodando FastAPI em containers Docker no ECS Fargate (2 tasks c5.xlarge com auto-scaling até 8); banco PostgreSQL 16 no RDS Multi-AZ com réplica de leitura; Redis para cache de sessões e filas; S3 para armazenamento de assets e backups; CDN Cloudflare com cache agressivo para conteúdo estático. Redes internas: VPC dedicada 10.0.0.0/16, subnet pública 10.0.1.0/24 (ALB e bastion), subnet privada 10.0.2.0/24 (aplicação e banco). Bastion host para acesso SSH: 10.0.1.50 (IP público via Elastic IP alocado). Pipeline de CI/CD: GitHub Actions disparando deploy automático no ECS após merge na branch main, com stage de testes unitários e lint obrigatórios.

## Próximos Lançamentos e Roadmap

Roadmap aprovado para 2026-2027: LLMAS Advanced Edition — previsão de lançamento outubro/2026, foco em ataques a sistemas multi-agentes, RAG poisoning com dados adversariais e manipulação de pipelines de IA em produção; preço de lançamento R$ 1.890,00. AI4CSP AD Edition — aguardando contratação do instrutor especialista em Active Directory (processo seletivo previsto para julho/2026); lançamento estimado Q1/2027. Trilha Expert — certificação de nível avançado com exame prático de 8 horas, prevista para Q2/2027, voltada a profissionais que já concluíram pelo menos dois cursos da Pandora. Expansão ibero-americana — análise de mercado prevista para Q3/2026, com foco em Chile, Colômbia e Portugal como mercados prioritários.
