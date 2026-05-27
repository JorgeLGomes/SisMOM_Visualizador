# Instruções para subir esta sessão no Git

**Repo:** `https://github.com/JorgeLGomes/SisMOM_Visualizador.git`
**Branch:** `main`

## 1. Verificar status (opcional)
```powershell
cd C:\Projetos\Visualizador
git status
```

Você deve ver `figuras_SisMOM_v23.html`, `electron-app/figuras_SisMOM_v23.html` modificados, mais arquivos novos em `dev/`.

## 2. Stage de tudo
```powershell
git add -A
```

## 3. Commits organizados (recomendado)

Faça **um commit por feature** — mais fácil reverter pontualmente depois:

### (a) Fase 5: painel direito controla o Mi ativo
```powershell
git add figuras_SisMOM_v23.html electron-app/figuras_SisMOM_v23.html dev/patch_active_panel.py dev/patch_active_panel_controls.py dev/patch_sidebar_left_fix.py dev/patch_sidebar_hide_preview.py dev/patch_multi_panel_gtiff.py dev/patch_paletas_extras.py
git commit -m "Fase 5: painel direito (sidebar) controla o painel Mi ativo - paleta, min/max, UNDEF/clip por slot via gtRerenderSlot sem refetch; 10 paletas extras; multi-panel no modo GeoTIFF; sidebar lateral fixa"
```

### (b) Mapa-base e opacidade por painel Mi
```powershell
git add dev/patch_per_slot_map.py
git commit -m "Mapa-base e opacidade por painel Mi - canvas SisMOM_Map por slot com tiles, fitTo(bbox) e setRasterOverlay; toggle/provider/opacidade salvos em gtSlotState"
```

### (c) Reposicionar pin "Painel Mi"
```powershell
git add dev/patch_panel_pin_pos.py
git commit -m "Reposicionar pin 'Painel Mi' para o canto superior esquerdo do map-body, fora dos icones do header"
```

### (d) Docs e meta
```powershell
git add BRIEFING_SESSAO.md RESUMO_RETOMAR.md docs/ .gitignore COMO-USAR.txt SisMOM.bat electron-app/main.js vendor/
git commit -m "Docs: PDF da documentacao, briefing atualizado; meta: .gitignore, scripts e Electron"
```

## 4. Atalho — UM commit só (se preferir)

Em vez de (a)–(d), você pode fazer:
```powershell
git add -A
git commit -m "Modo GeoTIFF: sidebar de controles por painel Mi ativo, mapa-base com tiles e opacidade por slot, pin reposicionado, paletas e patches lockstep"
```

## 5. Push
```powershell
git push origin main
```

## 6. Verificar
```powershell
git log --oneline -10
```

## Sequência mínima copy-paste (se for único commit)
```powershell
cd C:\Projetos\Visualizador
git add -A
git commit -m "Modo GeoTIFF: sidebar de controles por painel Mi, mapa-base por slot, pin reposicionado"
git push origin main
```

## Notas

- `electron-app/dist/`, `node_modules/`, `*.zip` já estão no `.gitignore` — não vão subir.
- Há uma pasta órfã `SisMOM_Visualizador/.git/` aninhada no repo (de um clone antigo); ela não interfere mas pode ser removida com:
  ```powershell
  Remove-Item -Recurse -Force C:\Projetos\Visualizador\SisMOM_Visualizador
  ```
- Se aparecer pedido de credenciais, use seu PAT (Personal Access Token) do GitHub no lugar da senha.
