## Visão Geral

- **Organização de Músicas:** Separa os arquivos musicais por artista e álbum.
- **Renomeação e Numeração de Faixas:** Corrige os metadados e padroniza os nomes dos arquivos, facilitando a navegação em aparelhos de som.
- **Otimização para Pen Drives:** Oferece duas opções de operação:
  - **Formatar o pen drive:** Apaga todo o conteúdo antes de copiar as músicas.
  - **Adicionar músicas:** Copia novas músicas sem apagar o conteúdo já existente.
- **Exibição de Progresso Detalhado:** Acompanha todo o processo com barra de progresso interativa.
- **Busca de Metadados Online:** Utiliza múltiplas APIs (Last.fm, MusicBrainz, Discogs, TheAudioDB) para identificar e corrigir automaticamente artistas, álbuns e títulos.

---

## Funcionalidades

- **Interface Gráfica com Tkinter:** Simples, intuitiva e elegante com design moderno.
- **Verificação de Privilégios Administrativos:** Garante que o script seja executado com as permissões necessárias para operações de sistema, como a formatação do pen drive.
- **Fluxo de Trabalho Guiado:** Interface passo a passo que orienta o usuário durante todo o processo.
- **Busca de Metadados Integrada:** Combina múltiplas fontes para enriquecer seus arquivos de música:
  - Last.fm: Para informações detalhadas sobre artistas e músicas
  - MusicBrainz: Para metadados precisos de álbuns e faixas
  - Discogs: Para capas de álbum e informações adicionais
  - TheAudioDB: Como fonte adicional de informações
- **Download de Capas de Álbum:** Busca e baixa automaticamente capas de álbum para cada pasta organizada.
- **Detecção de Idioma:** Identifica o idioma das músicas para melhor organização.
- **Monitoramento do Progresso:** Barra de progresso detalhada durante o processamento e cópia dos arquivos.
- **Renomeação de Pen Drive:** Permite definir um nome personalizado para o dispositivo.

---

## Requisitos e Dependências

### Sistema Operacional
- **Windows:** Desenvolvido e testado para Windows 10 ou superior.  
  *Observação:* É necessário executar o script com privilégios de administrador.

### Softwares e Bibliotecas
- **Python 3.x** – [Download Python](https://www.python.org/downloads/)
- **Tkinter:** Geralmente incluído com o Python em ambientes Windows.
- **Mutagen:** Para manipulação de metadados de arquivos de áudio.  
  ```bash
  pip install mutagen
  ```
- **Requests:** Para realizar requisições às APIs de metadados.  
  ```bash
  pip install requests
  ```

---

## Instalação e Configuração

### 1. Obtenha o Arquivo

O script principal está disponível como um único arquivo chamado `meloburn.py` neste repositório. Para baixar:
   - Clique no arquivo `meloburn.py` no repositório.
   - Selecione a opção **Raw** e salve o arquivo (Ctrl+S) em seu computador.

### 2. (Opcional) Crie um Ambiente Virtual

Abra o **Prompt de Comando** e execute:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instale as Dependências

Instale as bibliotecas necessárias com os seguintes comandos:
```bash
pip install mutagen requests
```

### 4. Chaves de API (Opcional)

O programa já vem com chaves de API padrão configuradas para:
- Last.fm
- Discogs
- MusicBrainz

Se você quiser usar suas próprias chaves, você pode editar o código-fonte e substituir os valores no dicionário `API_KEYS` no início do arquivo.

### 5. Permissões Administrativas

**Importante:** Para a formatação do pen drive e outras operações de sistema, o script deve ser executado com privilégios de administrador.  
- O aplicativo irá solicitar automaticamente privilégios de administrador quando necessário.
- Se preferir, clique com o botão direito no **Prompt de Comando** e selecione "Executar como administrador" antes de iniciar o script.

---

## Como Utilizar

### Opção 1: Executando com Interface Gráfica

1. **Iniciar o Programa:**
   - Clique duas vezes no arquivo `meloburn.py` ou execute-o via linha de comando
   - Se necessário, confirme a solicitação de privilégios administrativos

2. **Navegação pela Interface:**
   - **Tela de Boas-vindas:** Clique em "Iniciar" para começar o processo
   - **Etapa 1:** Selecione a pasta de origem que contém seus arquivos de música
   - **Etapa 2:** Selecione o pen drive ou dispositivo de destino
   - **Etapa 3:** Escolha o modo de operação (formatar ou adicionar) e defina um nome para o dispositivo
   - **Resumo:** Verifique as opções selecionadas e clique em "Iniciar Processo"

3. **Durante o Processo:**
   - Aguarde enquanto o aplicativo analisa, organiza e copia seus arquivos
   - A janela de progresso mostrará informações detalhadas sobre cada etapa
   - Você pode cancelar o processo a qualquer momento clicando no botão "Cancelar"

### Opção 2: Criando um Atalho com Privilégios Administrativos

Para garantir que o Meloburn seja sempre executado com as permissões necessárias:

1. **Criar um Atalho:**
   - Navegue até o arquivo `meloburn.py`
   - Clique com o botão direito sobre ele e selecione **"Criar atalho"**
   - Clique com o botão direito no atalho criado e escolha **"Propriedades"**
   - Na aba **"Compatibilidade"**, marque a opção **"Executar este programa como administrador"**
   - Clique em **"OK"** para salvar as alterações

2. **Executar via Atalho:**
   - Basta clicar duas vezes no atalho para iniciar o programa com privilégios administrativos

---

## Recursos Técnicos Adicionais

- **Cache de Metadados:** O programa salva um cache de pesquisas anteriores para melhorar o desempenho.
- **Processamento Multi-fonte:** Combina dados de várias APIs para resultados mais precisos.
- **Detecção de Idioma:** Algoritmo básico para identificar o idioma com base em palavras comuns.
- **Sanitização de Nomes de Arquivo:** Garante nomes de arquivo compatíveis com sistemas de arquivos.
- **Manipulação de Vários Formatos:** Suporta MP3, FLAC, WAV, AAC, OGG, M4A e WMA.

---

## Contato

Para dúvidas, sugestões ou problemas, entre em contato:

📩 **[t.me/adassecus](https://t.me/adassecus)**
