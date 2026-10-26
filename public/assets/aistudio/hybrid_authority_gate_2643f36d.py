from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import struct
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [EARTH-GATE] %(message)s")

class InvariantAuthorityHTTPHandler(BaseHTTPRequestHandler):
    """
    Upgraded Earth socket handler capable of processing binary V-Chip payloads
    wrapped inside standard enterprise HTTP request frameworks.
    """
    def do_POST(self):
        # Extract content length to safely pull data off the network socket
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self._send_response_packet(400, b"ERROR: empty_payload")
            return

        raw_body = self.rfile.read(content_length)
        
        try:
            # Parse the inner V-Chip frame layout out of the HTTP body envelope
            magic_byte, packet_length = struct.unpack("!BI", raw_body[0:5])
            
            if magic_byte == 0x51:
                json_payload = raw_body[5:5+packet_length].decode('utf-8')
                transaction_data = json.loads(json_payload)
                
                # Forward to the CAPPO evaluation space
                epoch = transaction_data.get("epoch")
                step = transaction_data.get("step")
                
                # --- This is where the execution tracers enter your logs ---
                logging.info(f"[LOG-TRACE] Timeline packet extracted successfully: Step {step} | Epoch {epoch}")
                
                # Simulate a successful execution log update to the state engine
                # In a live setup, this increments the SINK_OPS index directly
                self._send_response_packet(200, b"SUCCESS_COLLAPSE_LOGGED")
            else:
                logging.warning(f"[REJECT] Standard HTTP verified but inner magic byte mismatch: {magic_byte}")
                self._send_response_packet(422, b"ERROR: invalid_inner_geometry")
                
        except Exception as e:
            logging.error(f"[CRITICAL] Failed to parse wrapped stream context: {e}")
            self._send_response_packet(500, b"ERROR: structural_parse_failure")

    def _send_response_packet(self, status_code: int, message: bytes):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(message)))
        self.end_headers()
        self.wfile.write(message)

if __name__ == '__main__':
    # Binding to 0.0.0.0 so Mars can hit it across the physical network boundary
    server = ThreadingHTTPServer(('0.0.0.0', 8080), InvariantAuthorityHTTPHandler)
    logging.info("Hybrid Gate booted. Listening for 0x51-wrapped POSTs on 0.0.0.0:8080...")
    server.serve_forever()
