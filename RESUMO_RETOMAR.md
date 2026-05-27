# Resumo — SisMOM Visualizador (para retomar após reboot)

> Gerado em 2026-05-27, ao final de uma sessão de limpeza de artefatos de build.
> Contexto completo: `BRIEFING_SESSAO.md` neste mesmo diretório.

**Pasta de trabalho:** `C:\Projetos\Visualizador`

---

## O que foi feito nesta sessão (limpeza de artefatos)

| Ação | Resultado |
|---|---|
| Removido `electron-app/dist.zip` | −331 MB |
| Removido conteúdo da pasta-monstro `git commit -m Remove...` | −959 MB (restam ~1 MB locked em 2 `app.asar`) |
| Atualizado `.gitignore` com `*.zip`, `dist.zip`, `_dist_old*/`, `git commit*/` | Previne reincidência |
| **Total liberado** | **~1,29 GB** |

Origem da pasta-monstro: `npm run dist:win > "git commit -m ..."` no PowerShell — o redirect com aspas duplas virou nome de pasta em vez de comando.

Memórias persistentes criadas em `~/.claude/projects/C--Users-jorge-Downloads-etafcst/memory/`:
`user_jorge`, `project_sismom`, `feedback_html_lockstep`, `feedback_patch_workflow`, `reference_briefing`.

---

## 1º passo após o reboot — finalizar a limpeza

Os 2 `app.asar` remanescentes estavam locked (provavelmente Defender/Search Indexer). Reboot libera. Depois:

```powershell
Remove-Item -LiteralPath "C:\Projetos\Visualizador\electron-app\git commit -m Remove o modelo 'merge' do conjunto padrão de fábrica" -Recurse -Force
```

Confirmar que sumiu:
```powershell
cd C:\Projetos\Visualizador; git status
```

---

## Estado do repositório (não-commitado)

- ✏️ **Modificados:**
  - `.gitignore`
  - `BRIEFING_SESSAO.md`
  - `figuras_SisMOM_v23.html` (raiz)
  - `electron-app/figuras_SisMOM_v23.html`
  - **~1377 linhas de diff** nos dois HTMLs (idênticos entre si, lockstep ok)
- 📁 **Untracked em `dev/`:** 16 scripts `patch_*.py` + `inspect_tiff.mjs`
- 📁 **Untracked outros:** `vendor/`

Esse diff contém todo o trabalho descrito no `BRIEFING_SESSAO.md` após o commit `294c3b9`:
GeoTIFF dashboard, tiles XYZ, HUD inferior, colorbar com ticks adaptativos, camadas extras (GeoTIFF + GeoJSON), painel lateral colapsável, pan/zoom no canvas sem mapa, navegação corrigida em bbox global, multi-sentinel + min/max por percentil, etc.

Último commit no `main`: `294c3b9 Painel lateral colapsavel + reordenacao + controles por camada ativa`

---

## Frentes possíveis para a próxima sessão

1. **Commitar o pendente** — preferir vários commits temáticos (HUD, camadas, navegação, multi-sentinel) em vez de um commit gigante. Os nomes dos patches em `dev/patch_*.py` já sugerem a granularidade.
2. **Testar o estado atual** — abrir o HTML local e validar:
   - GeoTIFF com múltiplos sentinels (`Eta10_C00_PREC_2015020201.tif` mencionado no briefing)
   - Navegação em bbox global (sem mais ver lon=129° na Argentina)
   - Camadas extras: add/remove/reorder/clip/colorbar
3. **Nova feature** — a definir.

---

## Lembretes operacionais (não esquecer)

- Sempre patchear **as duas cópias** do HTML (raiz + `electron-app/`); validar com `diff -q figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html` (deve retornar vazio)
- Mudanças não-triviais via script Python em `dev/patch_*.py` (idempotente, **indentação 8 espaços** no IIFE — patches com 4 falham silenciosamente)
- Build Linux: WSL ou Docker, **nunca** Windows nativo (falta `mksquashfs` etc.)
- Não rodar build dentro do OneDrive (já corrompeu projeto no passado)
- **Cuidado com redirect no PowerShell** — não usar aspas em volta do nome após `>` ou nasce outra pasta-monstro
- Cópia legada em `C:\Users\jorge\OneDrive\Projetos\SisMOM\2026\Meta4\Visualizador` — **não buildar lá**
