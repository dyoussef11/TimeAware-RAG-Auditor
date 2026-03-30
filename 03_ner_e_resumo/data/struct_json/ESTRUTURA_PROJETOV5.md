# Estrutura do JSON: acer_16_predator_neo.json

## 1. Hierarquia Visual
```text
└── modelo_busca_utilizado [str]
└── posts [list]
    └── [Exemplo de item na lista: dict]
        └── id [str]
        └── titulo [str]
        └── conteudo_post [str]
        └── subreddit [str]
        └── flair [str]
        └── score [int]
        └── upvote_ratio [float]
        └── num_comments [int]
        └── categoria [str]
        └── url [str]
        └── data_post [float]
        └── comentarios [list]
            └── [Exemplo de item na lista: dict]
                └── id [str]
                └── conteudo [str]
                └── score [int]
                └── data_comentario [float]
```

---

## 2. Dicionário de Campos
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `modelo_busca_utilizado` | `str` | |
| `posts` | `list` | |
| `posts[].id` | `str` | |
| `posts[].titulo` | `str` | |
| `posts[].conteudo_post` | `str` | |
| `posts[].subreddit` | `str` | |
| `posts[].flair` | `str` | |
| `posts[].score` | `int` | |
| `posts[].upvote_ratio` | `float` | |
| `posts[].num_comments` | `int` | |
| `posts[].categoria` | `str` | |
| `posts[].url` | `str` | |
| `posts[].data_post` | `float` | |
| `posts[].comentarios` | `list` | |
| `posts[].comentarios[].id` | `str` | |
| `posts[].comentarios[].conteudo` | `str` | |
| `posts[].comentarios[].score` | `int` | |
| `posts[].comentarios[].data_comentario` | `float` | |
