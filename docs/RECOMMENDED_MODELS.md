# Recommended LLM Models for AgenticCTI

This guide provides recommendations for LLM models optimized for cyber threat intelligence analysis and malware investigation.

## Hardware Requirements

The recommendations below are optimized for systems with:
- **16 GB RAM** (minimum recommended)
- **NVIDIA RTX 4070 Ti Super** or equivalent GPU
- Models use Q4_K_M quantization for optimal performance/quality balance

## 1. Primary CTI Analysis Models

### ALIENTELLIGENCE/cybersecuritythreatanalysisv2 (Recommended Daily Driver)

**Purpose**: Your primary CTI assistant for daily threat intelligence operations.

**Best Use Cases**:
- ✅ Summarizing vendor threat reports and security blogs
- ✅ Extracting IOCs (IPs, URLs, domains, file hashes) into JSON/CSV
- ✅ Mapping TTPs to MITRE ATT&CK framework
- ✅ Drafting incident summaries and security advisories
- ✅ Creating playbook steps and response procedures
- ✅ Entity extraction (threat actors, malware families, campaigns)

**Performance**:
- Size is in the "easy" range for 16 GB systems
- Supports 8k+ context window
- Fast inference suitable for real-time analysis

**Installation**:
```bash
# Pull the v2 model (recommended)
ollama pull ALIENTELLIGENCE/cybersecuritythreatanalysisv2

# Or test v1 for comparison
ollama pull ALIENTELLIGENCE/cybersecuritythreatanalysis
```

**Configuration in AgenticCTI**:
```bash
# .env file
LLM_PROVIDER=ollama
LLM_MODEL=ALIENTELLIGENCE/cybersecuritythreatanalysisv2
LLM_BASE_URL=http://localhost:11434
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=8192
```

**Example Usage**:
```bash
# Run interactively
ollama run ALIENTELLIGENCE/cybersecuritythreatanalysisv2

# Test with AgenticCTI
docker exec -it agentic-cti-ollama ollama pull ALIENTELLIGENCE/cybersecuritythreatanalysisv2
```

## 2. Code Analysis & Malware Investigation Models

For malware analysis, reverse engineering, and writing detection rules, use one of these models alongside your primary CTI model:

### Option A: qwen2.5-coder:14b (Balanced - Recommended)

**Purpose**: Fast and capable code analysis for technical security work.

**Best Use Cases**:
- ✅ Explaining malware scripts and shellcode
- ✅ Deobfuscation assistance
- ✅ Reverse engineering notes and documentation
- ✅ Writing detection rules (YARA, Sigma, Suricata)
- ✅ Creating triage scripts (Python, PowerShell, Bash)
- ✅ Analyzing suspicious code samples
- ✅ API and system call analysis

**Performance**:
- 14B parameters with Q4_K_M quantization
- Excellent balance of speed and quality
- Well-suited for RTX 4070 Ti Super

**Installation**:
```bash
# Pull the model
ollama pull qwen2.5-coder:14b-q4_K_M

# Alternative: latest version
ollama pull qwen2.5-coder:14b
```

**Configuration**:
```bash
# For malware analysis tasks
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5-coder:14b-q4_K_M
LLM_BASE_URL=http://localhost:11434
LLM_TEMPERATURE=0.1  # Lower for code analysis
LLM_MAX_TOKENS=16384
```

**Example Use Cases**:
```python
# Deobfuscate JavaScript malware
prompt = """
Analyze this obfuscated JavaScript and explain what it does:

var _0x4d8e=['push','shift',...];
(function(_0x3a2b05,_0x4d8e2f){...})(_0x4d8e,0x1a3);
"""

# Write YARA rule
prompt = """
Create a YARA rule to detect this malware pattern:
- Uses WMI for persistence
- Connects to C2 at evil.com
- Encrypts files with .locked extension
"""

# Explain shellcode
prompt = """
Explain this x86 shellcode in detail:
\\x31\\xc0\\x50\\x68\\x2f\\x2f\\x73\\x68...
"""
```

### Option B: gpt-oss:20b (Maximum Quality)

**Purpose**: Maximum reasoning capability for complex investigations.

**Best Use Cases**:
- ✅ Long, multi-step investigation workflows
- ✅ Complex code analysis with large decompiled outputs
- ✅ Detailed explanations of sophisticated malware
- ✅ Analysis of large log files and forensic data
- ✅ Advanced threat hunting scenarios
- ✅ Comprehensive reverse engineering documentation

**Performance**:
- 20B parameters with Q4_K_M quantization
- Slower but more thorough than qwen2.5-coder
- Still comfortable on RTX 4070 Ti Super
- Best for quality over speed

**Installation**:
```bash
# Pull the model
ollama pull gpt-oss:20b-q4_K_M

# Alternative: latest version
ollama pull gpt-oss:20b
```

**Configuration**:
```bash
# For deep analysis tasks
LLM_PROVIDER=ollama
LLM_MODEL=gpt-oss:20b-q4_K_M
LLM_BASE_URL=http://localhost:11434
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=32768
```

**When to Use gpt-oss:20b**:
- Analyzing large decompiled binaries (IDA/Ghidra output)
- Multi-stage malware with complex logic
- APT campaign analysis requiring deep reasoning
- Forensic timeline reconstruction
- Correlating multiple data sources

## 3. Recommended Model Combinations

### Setup 1: Daily CTI Operations (Recommended for Most Users)
```bash
# Primary model for CTI
ollama pull ALIENTELLIGENCE/cybersecuritythreatanalysisv2

# Code/malware analysis
ollama pull qwen2.5-coder:14b-q4_K_M
```

**Use Case**: General CTI work with occasional malware analysis.

### Setup 2: Advanced Threat Research
```bash
# Primary CTI
ollama pull ALIENTELLIGENCE/cybersecuritythreatanalysisv2

# Deep malware analysis
ollama pull gpt-oss:20b-q4_K_M
```

**Use Case**: Advanced persistent threat research, complex malware families, forensic investigations.

### Setup 3: Comprehensive (All Bases Covered)
```bash
# Primary CTI
ollama pull ALIENTELLIGENCE/cybersecuritythreatanalysisv2

# Fast code analysis
ollama pull qwen2.5-coder:14b-q4_K_M

# Deep analysis
ollama pull gpt-oss:20b-q4_K_M
```

**Use Case**: Full-spectrum CTI and malware analysis capability.

## 4. Model Selection in AgenticCTI

### Dynamic Model Switching

You can configure different models for different tasks:

```python
# config/model_profiles.yaml
profiles:
  cti_analysis:
    model: "ALIENTELLIGENCE/cybersecuritythreatanalysisv2"
    temperature: 0.3
    max_tokens: 8192

  code_analysis:
    model: "qwen2.5-coder:14b-q4_K_M"
    temperature: 0.1
    max_tokens: 16384

  deep_investigation:
    model: "gpt-oss:20b-q4_K_M"
    temperature: 0.2
    max_tokens: 32768
```

### Environment Configuration

```bash
# .env - Set your default model
LLM_MODEL=ALIENTELLIGENCE/cybersecuritythreatanalysisv2

# Override for specific tasks via API
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://malware-sample.com",
    "options": {
      "llm_model": "qwen2.5-coder:14b-q4_K_M"
    }
  }'
```

## 5. Performance Optimization

### Memory Management

For 16 GB systems running multiple models:

```bash
# Set Ollama to limit concurrent models
export OLLAMA_MAX_LOADED_MODELS=2
export OLLAMA_NUM_PARALLEL=1

# Or in docker-compose.yml
environment:
  - OLLAMA_MAX_LOADED_MODELS=2
  - OLLAMA_NUM_PARALLEL=1
```

### GPU Acceleration

Ensure CUDA is properly configured:

```bash
# Check NVIDIA driver
nvidia-smi

# Verify Ollama sees GPU
docker exec -it agentic-cti-ollama nvidia-smi

# Monitor GPU usage during inference
watch -n 1 nvidia-smi
```

### Context Window Optimization

```bash
# For long documents
LLM_MAX_TOKENS=32768  # Use with gpt-oss:20b

# For rapid entity extraction
LLM_MAX_TOKENS=4096   # Faster with cybersecuritythreatanalysisv2

# For code analysis
LLM_MAX_TOKENS=16384  # Good balance for qwen2.5-coder
```

## 6. Benchmarks & Comparisons

### CTI Task Performance (Relative Speed)

| Model | IOC Extraction | TTP Mapping | Report Summary | Avg Speed |
|-------|----------------|-------------|----------------|-----------|
| cybersecuritythreatanalysisv2 | ⚡⚡⚡⚡⚡ | ⚡⚡⚡⚡⚡ | ⚡⚡⚡⚡⚡ | Fastest |
| qwen2.5-coder:14b | ⚡⚡⚡⚡ | ⚡⚡⚡ | ⚡⚡⚡⚡ | Fast |
| gpt-oss:20b | ⚡⚡⚡ | ⚡⚡⚡⚡ | ⚡⚡⚡⚡⚡ | Moderate |

### Code Analysis Quality (Relative)

| Model | Deobfuscation | Rule Writing | Shellcode Analysis | Quality |
|-------|---------------|--------------|-------------------|---------|
| cybersecuritythreatanalysisv2 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Good |
| qwen2.5-coder:14b | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Excellent |
| gpt-oss:20b | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Outstanding |

## 7. Troubleshooting

### Model Not Loading

```bash
# Check Ollama status
docker exec -it agentic-cti-ollama ollama list

# Restart Ollama
docker restart agentic-cti-ollama

# Re-pull model
docker exec -it agentic-cti-ollama ollama pull MODEL_NAME
```

### Out of Memory Errors

```bash
# Use smaller quantization
ollama pull MODEL_NAME:q4_0  # Smaller than q4_K_M

# Or reduce context window
LLM_MAX_TOKENS=4096

# Or close other applications
```

### Slow Inference

```bash
# Check GPU utilization
nvidia-smi

# Ensure GPU is being used
docker exec -it agentic-cti-ollama nvidia-smi

# Try smaller model
ollama pull qwen2.5-coder:7b  # Faster than 14b
```

## 8. Additional Resources

- **Ollama Model Library**: https://ollama.com/library
- **ALIENTELLIGENCE Models**: https://ollama.com/ALIENTELLIGENCE
- **Qwen2.5 Documentation**: https://qwenlm.github.io/
- **AgenticCTI Integration Guide**: [INTEGRATION_GUIDE.md](../INTEGRATION_GUIDE.md)

## 9. Model Updates

Models are regularly updated. Check for new versions:

```bash
# Update all models
ollama list | grep -v 'NAME' | awk '{print $1}' | xargs -I {} ollama pull {}

# Update specific model
ollama pull ALIENTELLIGENCE/cybersecuritythreatanalysisv2
```

## 10. Contributing

Have experience with other models? Please contribute your findings:
- Open an issue with benchmark results
- Submit a PR with model recommendations
- Share your use cases and configurations

---

**Last Updated**: 2025-12-29
**Tested Hardware**: NVIDIA RTX 4070 Ti Super, 16GB RAM
**Ollama Version**: Latest stable
