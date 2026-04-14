#!/usr/bin/env python3
"""
Discovery Mad-Libs Engine
=========================
A standalone discovery system for agents and humans.

Usage:
  python3 discovery.py --interactive          # Walk through onboarding
  python3 discovery.py --session PATH         # Resume a session
  python3 discovery.py --rewind-to N --redirect "why wrong"  # Rewind and redirect
  python3 discovery.py --let-run              # Run without stopping
  python3 discovery.py --check                # Review latest discoveries
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
TEMPLATES = BASE / "templates"
SESSIONS = BASE / "sessions"

DEEPINFRA_KEY = os.environ.get("DEEPINFRA_API_KEY", "")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

# ─── LLM Calls (curl-based, works reliably) ───

def call_llm(prompt, model="meta-llama/Llama-3.3-70B-Instruct-Turbo", max_tokens=2000):
    """Call an LLM via DeepInfra."""
    key = DEEPINFRA_KEY
    if not key:
        return "ERROR: No API key"
    body = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 0.8,
    })
    try:
        r = subprocess.run(
            ["curl", "-s", "-X", "POST",
             "https://api.deepinfra.com/v1/openai/chat/completions",
             "-H", f"Authorization: Bearer {key}",
             "-H", "Content-Type: application/json",
             "-d", body],
            capture_output=True, text=True, timeout=120
        )
        resp = json.loads(r.stdout)
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"

# ─── GPU Experiment Runner ───

def run_cuda(code, name, workdir):
    """Compile and run a CUDA experiment."""
    path = workdir / f"{name}.cu"
    binary = workdir / name
    path.write_text(code)
    r = subprocess.run(
        ["nvcc", "-O3", "-arch=sm_86", str(path), "-o", str(binary)],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        return f"COMPILE ERROR: {r.stderr[:500]}"
    r = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
    return r.stdout if r.returncode == 0 else f"RUN ERROR: {r.stderr}"

# ─── Session Management ───

def create_session(answers, template_name):
    """Create a new discovery session."""
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    slug = answers.get("quest", "discovery")[:30].lower().replace(" ", "-").replace("?", "")
    session_dir = SESSIONS / f"{ts}_{slug}"
    session_dir.mkdir(parents=True)
    (session_dir / "discoveries").mkdir()
    
    session = {
        "created": ts,
        "template": template_name,
        "quest": answers.get("quest", ""),
        "answers": answers,
        "status": "ready",
        "iteration": 0,
        "branchpoints": [],
    }
    (session_dir / "SESSION.json").write_text(json.dumps(session, indent=2))
    
    # Write human-readable session summary
    (session_dir / "SESSION.md").write_text(f"# Discovery Session: {answers.get('quest', '')}\n\n"
        f"**Template:** {template_name}\n"
        f"**Created:** {ts}\n"
        f"**Context:** {answers.get('context', '')}\n"
        f"**Success:** {answers.get('success', '')}\n"
        f"**Dead ends:** {answers.get('dead_ends', '')}\n"
        f"**Tools:** {answers.get('tools', '')}\n"
        f"**Scope:** {answers.get('scope_iterations', '10')} iterations\n"
        f"**Audience:** {answers.get('audience', '')}\n"
        f"**Avoid:** {answers.get('avoid', '')}\n")
    
    return session_dir

def load_session(path):
    """Load an existing session."""
    sp = Path(path)
    session = json.loads((sp / "SESSION.json").read_text())
    return sp, session

def save_session(sp, session):
    (sp / "SESSION.json").write_text(json.dumps(session, indent=2))

# ─── Interactive Onboarding ───

def onboard():
    """Walk through the essential questions."""
    print("=" * 60)
    print("DISCOVERY MAD-LIBS — Onboarding")
    print("=" * 60)
    print()
    
    # List available templates
    templates = list(TEMPLATES.glob("*.json"))
    print("Available templates:")
    for i, t in enumerate(templates):
        info = json.loads(t.read_text())
        print(f"  {i+1}. {info['name']} — {info.get('description', '')}")
    print()
    
    choice = input("Choose template (number or name): ").strip()
    try:
        idx = int(choice) - 1
        template_file = templates[idx]
    except:
        template_file = TEMPLATES / f"{choice}.json"
    
    template = json.loads(template_file.read_text())
    print(f"\nTemplate: {template['name']}")
    print()
    
    # Ask the essential questions
    answers = {}
    for field, question in template.get("fields", {}).items():
        print(f"❓ {question}")
        answer = input("  → ").strip()
        answers[field] = answer
        print()
    
    # Create session
    session_dir = create_session(answers, template["name"])
    print(f"✅ Session created: {session_dir}")
    return session_dir, template

# ─── The Discovery Loop ───

def discover(session_dir, template, n_iterations=1, auto=False):
    """Run the discovery loop."""
    sp = Path(session_dir)
    session = json.loads((sp / "SESSION.json").read_text())
    
    system_prompt = template["system_prompt"].format(**session["answers"])
    discoveries = sorted((sp / "discoveries").glob("*.md"))
    previous = ""
    if discoveries:
        latest = discoveries[-1]
        previous = latest.read_text()
    
    for i in range(n_iterations):
        session["iteration"] += 1
        iteration = session["iteration"]
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        print(f"\n{'='*60}")
        print(f"DISCOVERY {iteration} | {ts}")
        print(f"{'='*60}")
        
        # Generate discovery
        discovery_prompt = template["discovery_prompt"].format(
            previous_discoveries=previous[-3000:] if previous else "(none yet)"
        )
        full_prompt = f"{system_prompt}\n\n{discovery_prompt}"
        
        print("  [1/3] Generating hypothesis...")
        discovery_text = call_llm(full_prompt)
        
        # If GPU enabled and CUDA code detected, run it
        gpu_result = None
        if template.get("gpu_enabled") and "```" in discovery_text:
            print("  [2/3] CUDA code detected, running experiment...")
            code = discovery_text
            if "```" in code:
                parts = code.split("```")
                for p in parts:
                    p = p.strip()
                    if p.startswith(("cuda", "cpp", "c")):
                        p = p.split("\n", 1)[1]
                    if "#include" in p or "__global__" in p:
                        code = p
                        break
            gpu_result = run_cuda(code, f"exp_{iteration:03d}", sp / "discoveries")
            print(f"  GPU result: {str(gpu_result)[:200]}")
        
        # Evaluate
        print("  [3/3] Evaluating...")
        result_text = discovery_text
        if gpu_result:
            result_text += f"\n\nGPU EXPERIMENT RESULT:\n{gpu_result}"
        
        eval_prompt = template["evaluation_prompt"].format(
            quest=session["answers"].get("quest", ""),
            hypothesis=discovery_text[:1000],
            result=result_text[:2000],
        )
        evaluation = call_llm(eval_prompt, max_tokens=1000)
        
        # Save discovery
        discovery_file = sp / "discoveries" / f"{iteration:03d}_{ts}.md"
        discovery_file.write_text(
            f"# Discovery {iteration}\n\n"
            f"**Time:** {ts}\n\n"
            f"## Hypothesis\n{discovery_text}\n\n"
            f"## GPU Result\n{gpu_result or 'N/A'}\n\n"
            f"## Evaluation\n{evaluation}\n"
        )
        
        # Parse evaluation for branch point
        try:
            start = evaluation.find("{")
            end = evaluation.rfind("}") + 1
            if start >= 0 and end > start:
                eval_json = json.loads(evaluation[start:end])
                verdict = eval_json.get("verdict", "UNKNOWN")
                alignment = eval_json.get("alignment", "on_track")
                
                print(f"  Verdict: {verdict}")
                print(f"  Alignment: {alignment}")
                
                # Record branch point
                session["branchpoints"].append({
                    "iteration": iteration,
                    "verdict": verdict,
                    "alignment": alignment,
                    "file": str(discovery_file),
                })
                
                # If drifting or off-track and not auto, pause
                if alignment in ("drifting", "off_track") and not auto:
                    print(f"\n⚠️  Engine reports: {alignment}")
                    print(f"Latest discovery may be off track. Review it:")
                    print(f"  cat {discovery_file}")
                    print(f"\nOptions:")
                    print(f"  --let-run     (trust the engine)")
                    print(f"  --rewind-to {iteration} --redirect \"your correction\"")
                    print(f"  --check       (review and decide)")
                    save_session(sp, session)
                    return
        except:
            pass
        
        previous = discovery_file.read_text()
        save_session(sp, session)
        
        if auto:
            print(f"  → Auto-continuing to next iteration...")
        else:
            cont = input(f"\n  Continue? (y/r=rewind/q=quit): ").strip().lower()
            if cont == 'q':
                break
            elif cont.startswith('r'):
                try:
                    rewind_to = int(cont.split()[1]) if len(cont.split()) > 1 else iteration - 1
                except:
                    rewind_to = iteration - 1
                redirect = input("  Why was this direction wrong? ").strip()
                rewind(sp, session, rewind_to, redirect)
                break
    
    session["status"] = "completed"
    save_session(sp, session)
    print(f"\n✅ Session complete. {session['iteration']} discoveries made.")

def rewind(session_dir, session, to_iteration, reason):
    """Rewind to a branch point and redirect."""
    sp = Path(session_dir)
    
    # Mark discoveries after the branch point as superseded
    for d in sorted((sp / "discoveries").glob("*.md")):
        num = int(d.name.split("_")[0])
        if num > to_iteration:
            # Move to superseded folder
            old_dir = sp / "discoveries" / "superseded"
            old_dir.mkdir(exist_ok=True)
            d.rename(old_dir / d.name)
    
    # Create redirect marker
    redirect_file = sp / "discoveries" / f"{to_iteration:03d}_REDIRECT.md"
    redirect_file.write_text(
        f"# REDIRECT at iteration {to_iteration}\n\n"
        f"**Reason:** {reason}\n\n"
        f"Previous direction was wrong. Starting fresh from here.\n"
    )
    
    session["iteration"] = to_iteration
    session["status"] = "redirected"
    session["branchpoints"].append({
        "iteration": to_iteration,
        "action": "redirect",
        "reason": reason,
    })
    save_session(sp, session)
    print(f"↩️  Rewound to iteration {to_iteration}. Reason: {reason}")

def check(session_dir):
    """Review latest discoveries."""
    sp = Path(session_dir)
    session = json.loads((sp / "SESSION.json").read_text())
    
    print(f"Session: {session['quest']}")
    print(f"Status: {session['status']}")
    print(f"Iterations: {session['iteration']}")
    print(f"Branch points: {len(session['branchpoints'])}")
    print()
    
    discoveries = sorted((sp / "discoveries").glob("*.md"))
    # Show last 3
    for d in discoveries[-3:]:
        print(f"--- {d.name} ---")
        print(d.read_text()[:500])
        print()

# ─── CLI ───

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Discovery Mad-Libs Engine")
    parser.add_argument("--interactive", action="store_true", help="Walk through onboarding")
    parser.add_argument("--session", type=str, help="Resume a session path")
    parser.add_argument("--rewind-to", type=int, help="Rewind to iteration N")
    parser.add_argument("--redirect", type=str, help="Why the direction was wrong")
    parser.add_argument("--let-run", action="store_true", help="Run without stopping")
    parser.add_argument("--check", action="store_true", help="Review latest discoveries")
    parser.add_argument("--iterations", type=int, default=10, help="Number of iterations")
    args = parser.parse_args()
    
    SESSIONS.mkdir(parents=True, exist_ok=True)
    
    if args.interactive:
        session_dir, template = onboard()
        discover(session_dir, template, n_iterations=args.iterations, auto=False)
    elif args.session:
        session_dir, session = load_session(args.session)
        template_file = TEMPLATES / f"{session['template']}.json"
        template = json.loads(template_file.read_text())
        
        if args.check:
            check(session_dir)
        elif args.rewind_to is not None:
            reason = args.redirect or "Direction was off track"
            rewind(session_dir, session, args.rewind_to, reason)
        else:
            discover(session_dir, template, n_iterations=args.iterations, auto=args.let_run)
    else:
        # Find latest session
        sessions = sorted(SESSIONS.iterdir())
        if sessions:
            latest = sessions[-1]
            print(f"Resuming latest session: {latest}")
            session, sdata = load_session(latest)
            template_file = TEMPLATES / f"{sdata['template']}.json"
            template = json.loads(template_file.read_text())
            discover(session, template, n_iterations=args.iterations, auto=args.let_run)
        else:
            print("No sessions found. Run with --interactive to start.")
