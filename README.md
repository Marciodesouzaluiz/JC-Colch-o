# Portal de Agendamento de Entregas — JC Colchão

## 📋 Visão Geral

Portal web desenvolvido em **Python + Flask** para fornecedores realizarem agendamento
de entregas de mercadorias para a JC Colchão (www.jccolchao.com.br).

---

## 🗂️ Estrutura do Projeto

```
jccolchao_portal/
├── app.py                    # Aplicação principal (rotas, modelos, lógica)
├── requirements.txt          # Dependências Python
├── instalar.bat              # Script de instalação (Windows)
├── iniciar.bat               # Script para iniciar o servidor
├── jccolchao.db              # Banco de dados SQLite (gerado automaticamente)
├── uploads/                  # Arquivos de nota fiscal enviados
├── static/
│   ├── css/                  # Estilos adicionais
│   ├── js/                   # Scripts adicionais
│   └── img/                  # Imagens / logo
└── templates/
    ├── base.html             # Layout base (navbar, footer)
    ├── index.html            # Página inicial
    ├── login.html            # Login de fornecedor
    ├── cadastro.html         # Cadastro de fornecedor
    ├── dashboard.html        # Painel do fornecedor
    ├── novo_agendamento.html # Formulário de agendamento
    ├── meus_agendamentos.html# Lista de agendamentos
    ├── detalhe_agendamento.html # Detalhes do agendamento
    ├── perfil.html           # Perfil do fornecedor
    └── admin/
        ├── base_admin.html   # Layout admin (sidebar)
        ├── login.html        # Login de administrador
        ├── dashboard.html    # Dashboard administrativo
        ├── agendamentos.html # Lista admin de agendamentos
        ├── detalhe.html      # Detalhe admin + mudança de status
        └── fornecedores.html # Gestão de fornecedores
```

---

## ⚙️ Instalação Passo a Passo

### 1. Instalar o Python

- Acesse: https://www.python.org/downloads/
- Baixe o **Python 3.10 ou superior**
- ✅ Durante a instalação, marque: **"Add Python to PATH"**
- ⚠️ NÃO instale pelo Microsoft Store (tem restrições de acesso)

### 2. Instalar as dependências

Abra o **Prompt de Comando** na pasta do projeto e execute:

```batch
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Ou simplesmente **clique duas vezes** em `instalar.bat`

### 3. Iniciar o servidor

```batch
venv\Scripts\activate
python app.py
```

Ou **clique duas vezes** em `iniciar.bat`

### 4. Acessar o portal

Abra o navegador em: **http://localhost:5000**

---

## 👤 Usuário Administrador Padrão

| Campo | Valor |
|-------|-------|
| E-mail | admin@jccolchao.com.br |
| Senha | admin@123 |

> ⚠️ **Altere a senha padrão antes de colocar em produção!**

### Acessar painel administrativo:
- URL: http://localhost:5000/admin/login

---

## 🔑 Funcionalidades

### Portal do Fornecedor
- ✅ Cadastro com CNPJ, razão social, e-mail e senha
- ✅ Login seguro com senha criptografada (bcrypt)
- ✅ Dashboard com estatísticas pessoais
- ✅ Novo agendamento com:
  - Data e horário de entrega
  - Dados da mercadoria (tipo, volumes, peso, valor)
  - Dados da transportadora e motorista
  - Upload de nota fiscal (PDF, XML, JPG, PNG) - drag & drop
- ✅ Listagem e filtro de agendamentos por status
- ✅ Detalhe do agendamento com timeline
- ✅ Cancelamento de agendamentos
- ✅ Edição de perfil e troca de senha

### Painel Administrativo (JC Colchão)
- ✅ Dashboard com KPIs em tempo real
- ✅ Lista completa de todos os agendamentos
- ✅ Filtro por status
- ✅ Visualização detalhada de cada agendamento
- ✅ Alteração de status com observação
  - Aguardando Aprovação → Aprovado / Reprovado / Entregue / Cancelado
- ✅ Download de nota fiscal
- ✅ Gestão de fornecedores (ativar/desativar)

### Status dos Agendamentos
| Status | Descrição |
|--------|-----------|
| 🟡 Aguardando Aprovação | Recém-criado pelo fornecedor |
| 🟢 Aprovado | Confirmado pela equipe JC Colchão |
| 🔴 Reprovado | Rejeitado com observação |
| 🔵 Entregue | Entrega confirmada |
| ⚫ Cancelado | Cancelado pelo fornecedor ou admin |

---

## 🚀 Deploy em Produção

Para publicar o portal no domínio www.jccolchao.com.br:

### Opção 1: VPS / Servidor Dedicado

1. Instale Python + Gunicorn + Nginx no servidor Linux
2. Configure o Gunicorn como servidor WSGI:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```
3. Configure o Nginx como proxy reverso
4. Configure o SSL com Let's Encrypt (HTTPS)

### Opção 2: Plataformas Cloud

- **Railway.app** — Deploy gratuito via GitHub
- **Render.com** — Suporte nativo ao Flask
- **PythonAnywhere.com** — Especializado em Python

### Variáveis de ambiente para produção

```bash
SECRET_KEY=chave-super-secreta-aleatoria-longa
DATABASE_URL=postgresql://...   # Para PostgreSQL em produção
```

---

## 🔒 Segurança

- Senhas armazenadas com hash Werkzeug (bcrypt)
- Arquivos enviados com nomes aleatórios (UUID)
- Validação de extensão de arquivo
- Proteção de acesso aos uploads (somente dono ou admin)
- Sessões protegidas por SECRET_KEY
- Limite de 10MB por arquivo

---

## 📞 Suporte

Portal desenvolvido para: **JC Colchão**
Site: www.jccolchao.com.br
