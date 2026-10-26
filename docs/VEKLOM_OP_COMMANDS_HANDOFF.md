# Veklom OP-Commands & Machine Execution Specification
# Target: veklom-op-commands / Machine-to-Machine (M2M) Engine

### 1. Scope & Objective
This agent handles the low-level, air-gapped operational command layer (veklom-op). 
It executes deterministic machine-to-machine handshakes, hardware-enclave operations, 
entropy-compressed state transitions, and offline validation routines without network packets.

### 2. Core Functional Responsibilities
- Optical State Ingestion & Decoding (HCC2D / vChip 17x17 grid photonics).
- Low-latency verification loop (<10ms target on ARM Cortex / embedded Linux).
- Ed25519 cryptographic root-of-trust signature verification.
- tANS (Asymmetric Numeral Systems) and CBOR binary decompression.
- Localized state-machine execution: updating machine registers based on scanned state-vectors.

### 3. Command Line Interface (CLI) & Machine Opcodes

#### A. Ingestion & Validation
`veklom-op scan --device=/dev/video0 --format=vchip-17x17 --verify-root=pubkey.pem`
- Ingests raw optical frame from camera/sensor.
- Validates 64-byte Ed25519 signature against local hardware enclave.
- Outputs exit code 0 (Authorized) or exit code 1 (Tampered/Invalid).

#### B. State-Vector Serialization
`veklom-op pack --in=state_snapshot.json --compress=tans --out=state_vector.bin`
- Compresses operational data payload into dense binary bitfield.
- Signs payload with local machine private key.
- Prepares carrier raster data for e-ink or micro-display rendering.

#### C. Deterministic M2M Handshake
`veklom-op handshake --target-id=ROBOT_ARM_04 --nonce=auto --timeout=15ms`
- Initiates optical emission burst.
- Listens for optical acknowledgment response.
- Executes mechanical trigger (e.g. valve release, latch open, payload handover).

#### D. Offline Proof-of-Life Telemetry
`veklom-op attest --telemetry=sensor_stream.log --timestamp=hardware-rtc --seal`
- Binds offline sensor logs with device root key.
- Generates Merkle state-root for offline compliance audits.

### 4. Technical Constraints & Standards
- Network: Strict zero-socket / air-gapped enforcement (no HTTP/TCP dependencies).
- Crypto: Ed25519 (signatures), AES-256-GCM (payload privacy), SHA-256 (leaf hashing).
- Ingestion Latency: Fixed budget <= 10ms for decode + verify.
- Resilience: Forward Error Correction (Reed-Solomon / LDPC) for optical surface wear.
