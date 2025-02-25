# Meloburn 🍯🎶

O **Meloburn** é uma aplicação gráfica desenvolvida em Python que organiza sua biblioteca musical de forma prática e inteligente. Com ele, você pode:
- **Organizar músicas:** Separa os arquivos musicais por artista e álbum.
- **Renomear e numerar faixas:** Corrige metadados e padroniza os nomes dos arquivos.
- **Otimizar para aparelhos de som:** Cria uma estrutura organizada e de fácil navegação.
- **Copiar para pen drive:** Oferece a opção de formatar o pen drive (apagando todos os dados) ou adicionar músicas mantendo o conteúdo existente.
- **Exibir logs detalhados:** Acompanha todo o processo de organização e cópia com mensagens interativas e informativas.

---

## Funcionalidades ✨

- **Interface Gráfica com Tkinter:** Fácil de usar e com design intuitivo.
- **Verificação de privilégios:** Garante que o script seja executado com permissões administrativas.
- **Busca e correção de metadados:** Utiliza a API do [TheAudioDB](https://www.theaudiodb.com/) para melhorar a identificação de artista e título das faixas.
- **Cópia com monitoramento de progresso:** Exibe uma barra de progresso durante a cópia dos arquivos para o pen drive.
- **Opção de exportação de log:** Permite salvar o registro das operações para consulta futura.

---

## Requisitos e Dependências ✔️

### Sistema Operacional
- **Windows:** Desenvolvido e testado para Windows.  
  **Versões recomendadas:** Windows 10 ou superior.  
  *Observação:* É necessário executar o script com privilégios de administrador.

### Softwares e Bibliotecas
- **Python 3.x** – [Download Python](https://www.python.org/downloads/)
- **Tkinter:** Geralmente incluído com o Python em ambientes Windows.
- **Mutagen:** Para manipulação de metadados (instalar via `pip install mutagen`)
- **Requests:** Para fazer requisições HTTP (instalar via `pip install requests`)
