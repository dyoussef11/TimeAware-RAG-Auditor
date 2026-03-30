# Estrutura do JSON: acer_acer16predatorneonh.qltsi.001_corei5_16.json

## 1. Hierarquia Visual
```text
└── modelo_original [str]
└── modelo_busca_utilizado [str]
└── id_notebook [str]
└── data_extracao [float]
└── config_time_filter [str]
└── api_health_at_extraction [dict]
│   └── restante [float]
│   └── reset_em [float]
└── total_posts_encontrados [int]
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
| `modelo_original` | `str` | |
| `modelo_busca_utilizado` | `str` | |
| `id_notebook` | `str` | |
| `data_extracao` | `float` | |
| `config_time_filter` | `str` | |
| `api_health_at_extraction` | `dict` | |
| `api_health_at_extraction.restante` | `float` | |
| `api_health_at_extraction.reset_em` | `float` | |
| `total_posts_encontrados` | `int` | |
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
