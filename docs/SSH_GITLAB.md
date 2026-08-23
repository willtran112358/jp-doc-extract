# Add SSH key on this laptop (git.vmo.dev)

GitLab currently has key **LAPTOP-5330** (other machine). This laptop needs its own key.

## 1. Public key (already generated)

File: `~/.ssh/id_ed25519_willtran_wov2.pub`

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAID0fyaoPRTsm8itq9fummYMMwZpAaGS1gNzEAPfqK4Zr bchin@WillTran-WOV2-OCR
```

## 2. Register on GitLab

1. Open https://git.vmo.dev/-/user_settings/ssh_keys  
2. Sign in with **VMO Gmail**  
3. **Add new key**  
   - Title: `WillTran-WOV2-OCR`  
   - Key: paste public key above  
   - Usage: Authentication  
4. Save

## 3. Test

```powershell
ssh -T git@git.vmo.dev
```

Expect a welcome / successful auth message (not `Permission denied`).

## 4. Create project + push PoC

1. Create empty project on GitLab, e.g. `clap-ai-ocr-poc`  
2. From repo folder:

```powershell
cd D:\bchin\Downloads\VMO\WOV2-AI\clap-ai-ocr-poc
git remote add origin git@git.vmo.dev:GROUP_OR_USER/clap-ai-ocr-poc.git
git push -u origin main
```

Replace `GROUP_OR_USER` with your GitLab path.
