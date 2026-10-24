"""Deploy only AFTER the frozen scoped study has completed."""
import modal
from .tatqa_scope_app import app,runtime,models,APP_NAME

@app.cls(image=runtime,volumes={'/models':models},gpu='L40S',cpu=2,memory=16384,
         timeout=600,max_containers=1,scaledown_window=60,retries=0)
class TatqaPlainReviewOllama:
    @modal.enter()
    def start(self):
        from .tatqa_plain_tools import start_server
        start_server(self,models,'/models/repguard_modern_manifest.json')
    @modal.exit()
    def stop(self):self.process.terminate()
    @modal.method()
    def solve(self,case,current=None):
        from .tatqa_plain_tools import solve_request
        return solve_request(self,case,current,'qwen3.5:27b',APP_NAME)
