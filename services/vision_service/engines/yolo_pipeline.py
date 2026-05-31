"""
BlindWatch YOLO + Frame Extraction Pipeline
--------------------------------------------
Handles:
  - RTSP stream ingestion
  - Webcam capture
  - Uploaded video file processing
  - Frame extraction at configurable FPS (5 / 10 / 15)
  - YOLOv8 object detection
  - Face detection + privacy anonymization (in-memory only, never stored)
  - ByteTrack-style entity tracking (lightweight fallback if not installed)

Dependencies (install as available):
  pip install ultralytics opencv-python-headless numpy
"""
import hashlib
import datetime
import threading
import time
import queue
import numpy as np
from typing import Dict, List, Optional, Callable, Tuple

# ── Optional heavy imports ─────────────────────────────────────────────────────
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from ultralytics import YOLO as _YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

# ── Detected class constants ───────────────────────────────────────────────────
DETECTABLE_CLASSES = {
    "person", "bag", "backpack", "knife", "gun", "pistol", "rifle",
    "fire", "smoke", "flame", "car", "truck", "bus", "motorcycle",
}

COCO_FACE_CLASSES = {"face"}   # When using a face-specific model


# ══════════════════════════════════════════════════════════════════════════════
# Frame Extractor
# ══════════════════════════════════════════════════════════════════════════════

class FrameExtractor:
    """
    Extracts frames from a video source at a configurable rate.
    Supports: RTSP URL, webcam index (int), local video file path.
    """

    SUPPORTED_FPS = (5, 10, 15)

    def __init__(self, source, target_fps: int = 5):
        assert target_fps in self.SUPPORTED_FPS, f"FPS must be one of {self.SUPPORTED_FPS}"
        self.source     = source
        self.target_fps = target_fps
        self._cap       = None
        self._running   = False

    def open(self) -> bool:
        if not CV2_AVAILABLE:
            return False
        self._cap = cv2.VideoCapture(self.source)
        return self._cap.isOpened()

    def release(self):
        if self._cap and CV2_AVAILABLE:
            self._cap.release()
        self._running = False

    def generate_frames(self, max_frames: Optional[int] = None):
        """
        Generator that yields (frame_index, timestamp, frame_ndarray) tuples.
        Skips frames to honour target_fps.
        """
        if not CV2_AVAILABLE or self._cap is None:
            return

        source_fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        step = max(1, int(source_fps / self.target_fps))
        frame_idx = 0
        yielded = 0

        while True:
            ret, frame = self._cap.read()
            if not ret:
                break
            if frame_idx % step == 0:
                yield frame_idx, datetime.datetime.utcnow(), frame
                yielded += 1
                if max_frames and yielded >= max_frames:
                    break
            frame_idx += 1


# ══════════════════════════════════════════════════════════════════════════════
# Object Detector (YOLOv8)
# ══════════════════════════════════════════════════════════════════════════════

class ObjectDetector:
    """
    Wraps YOLOv8 for object detection.
    Falls back to a lightweight mock when ultralytics is not installed.
    """

    DEFAULT_MODEL = "yolov8n.pt"   # nano – fast inference
    PROD_MODEL    = "yolov8m.pt"   # medium – higher accuracy

    def __init__(self, model_path: str = DEFAULT_MODEL):
        self.model_path = model_path
        self._model     = None
        self._load()

    def _load(self):
        if YOLO_AVAILABLE:
            try:
                self._model = _YOLO(self.model_path)
            except Exception as e:
                print(f"[YOLO] Model load failed: {e} – using mock detector")
                self._model = None

    def detect(self, frame: np.ndarray, conf_threshold: float = 0.50) -> List[Dict]:
        """
        Returns list of detection dicts:
          { class, confidence, bbox: [x1, y1, x2, y2] }
        """
        if self._model is not None and YOLO_AVAILABLE and CV2_AVAILABLE:
            results = self._model(frame, conf=conf_threshold, verbose=False)
            detections = []
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    cls_name = r.names[cls_id].lower()
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    detections.append({
                        "class":      cls_name,
                        "confidence": round(conf, 3),
                        "bbox":       [x1, y1, x2, y2],
                    })
            return detections

        # ── Mock detections (for environments without GPU / ultralytics) ──
        return self._mock_detections(frame)

    @staticmethod
    def _mock_detections(frame: np.ndarray) -> List[Dict]:
        """Deterministic mock – returns 1 person detection for unit testing."""
        h, w = (frame.shape[0], frame.shape[1]) if frame is not None else (480, 640)
        return [{
            "class":      "person",
            "confidence": 0.91,
            "bbox":       [int(w * 0.3), int(h * 0.2), int(w * 0.7), int(h * 0.9)],
        }]


# ══════════════════════════════════════════════════════════════════════════════
# Face Detector
# ══════════════════════════════════════════════════════════════════════════════

class FaceDetector:
    """
    Detects faces within a frame.
    Uses OpenCV's Haar cascade as a lightweight built-in option.
    Faces are returned as bounding boxes ONLY – never stored or logged.
    """

    def __init__(self):
        self._cascade = None
        if CV2_AVAILABLE:
            try:
                import os
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                if os.path.exists(cascade_path):
                    self._cascade = cv2.CascadeClassifier(cascade_path)
            except Exception:
                pass

    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Returns list of (x1, y1, x2, y2) face bounding boxes."""
        if not CV2_AVAILABLE or self._cascade is None or frame is None:
            return []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
        result = []
        for (x, y, w, h) in faces:
            result.append((x, y, x + w, y + h))
        return result


# ══════════════════════════════════════════════════════════════════════════════
# Lightweight ByteTrack-style Tracker
# ══════════════════════════════════════════════════════════════════════════════

class EntityTracker:
    """
    Tracks anonymous entities across frames using IoU-based matching.
    Assigns stable tracking IDs per session – IDs reset when tracker restarts.

    In production, replace with ultralytics' built-in ByteTrack via:
        model.track(frame, persist=True, tracker="bytetrack.yaml")
    """

    IOU_THRESHOLD = 0.30

    def __init__(self):
        self._tracks: Dict[int, Dict] = {}   # track_id → state
        self._next_id = 1

    @staticmethod
    def _iou(a: List[int], b: List[int]) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)
        if ix2 <= ix1 or iy2 <= iy1:
            return 0.0
        inter = (ix2 - ix1) * (iy2 - iy1)
        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    def update(self, detections: List[Dict]) -> List[Dict]:
        """
        Matches detections to existing tracks by IoU.
        Returns detections enriched with track_id and prev_bbox.
        """
        person_dets = [d for d in detections if d["class"] == "person"]
        updated_tracks = {}

        for det in person_dets:
            bbox = det["bbox"]
            best_id, best_iou = None, 0.0
            for tid, state in self._tracks.items():
                iou = self._iou(bbox, state["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_id = tid

            if best_iou >= self.IOU_THRESHOLD and best_id is not None:
                # Matched existing track
                track_id = best_id
                prev_bbox = self._tracks[best_id]["bbox"]
                self._tracks.pop(best_id)
            else:
                # New track
                track_id = self._next_id
                self._next_id += 1
                prev_bbox = bbox

            updated_tracks[track_id] = {"bbox": bbox, "class": det["class"]}
            det["track_id"]  = track_id
            det["prev_bbox"] = prev_bbox

        # Mark lost tracks (not seen this frame)
        # In production, implement track memory / Kalman prediction here
        self._tracks = updated_tracks

        return person_dets


# ══════════════════════════════════════════════════════════════════════════════
# Vision Pipeline – orchestrates all engines per frame
# ══════════════════════════════════════════════════════════════════════════════

class VisionPipeline:
    """
    End-to-end processing pipeline:
      Frame → Detection → Face Anonymize → Track → Risk → Threat → Event
    """

    def __init__(
        self,
        camera_id: str,
        camera_location: str,
        tenant_id: str,
        anonymization_mode: str = "blur",
        model_path: str = ObjectDetector.DEFAULT_MODEL,
        fps: int = 5,
        zones: Optional[List[Dict]] = None,
    ):
        from services.vision_service.engines.privacy_engine  import FaceAnonymizer, EntityHasher
        from services.vision_service.engines.risk_engine     import (
            RiskEngine, MovementEngine, ZoneEngine,
            ObjectInteractionEngine, CrowdAnalysisEngine, AnomalyEngine,
        )
        from services.vision_service.engines.threat_engine   import ThreatEngine, ExplainableAIEngine

        self.camera_id       = camera_id
        self.location        = camera_location
        self.tenant_id       = tenant_id
        self.fps             = fps
        self.zones           = zones or []
        self.anonymizer      = FaceAnonymizer(mode=anonymization_mode)
        self.hasher          = EntityHasher()
        self.detector        = ObjectDetector(model_path)
        self.face_detector   = FaceDetector()
        self.tracker         = EntityTracker()

    def process_frame(
        self,
        frame: np.ndarray,
        timestamp: datetime.datetime,
        on_event: Optional[Callable[[Dict], None]] = None,
    ) -> Dict:
        """
        Processes a single frame through the full AI pipeline.
        Returns a structured result dict.
        """
        from services.vision_service.engines.privacy_engine import FaceAnonymizer, EntityHasher
        from services.vision_service.engines.risk_engine import (
            RiskEngine, MovementEngine, ZoneEngine,
            ObjectInteractionEngine, CrowdAnalysisEngine, AnomalyEngine,
        )
        from services.vision_service.engines.threat_engine import ThreatEngine, ExplainableAIEngine

        # 1. Object detection
        detections = self.detector.detect(frame)

        # 2. Face detection + anonymization (in-memory, never stored)
        face_bboxes = self.face_detector.detect(frame)
        if frame is not None and face_bboxes:
            frame = self.anonymizer.anonymize(frame, face_bboxes)

        # 3. Entity tracking
        tracked = self.tracker.update(detections)

        # 4. Encode frame to JPEG base64 (after anonymization)
        frame_b64 = self._encode_frame(frame)

        # 5. Per-entity risk + threat computation
        entity_results = []
        all_events     = []

        people_count = len(tracked)
        crowd_result = CrowdAnalysisEngine.calculate(people_count)

        for det in tracked:
            bbox       = det["bbox"]
            track_id   = det["track_id"]
            prev_bbox  = det["prev_bbox"]

            # Generate anonymous entity hash
            entity_hash = self.hasher.generate(self.camera_id, track_id, timestamp)

            # Entity centre
            cx = (bbox[0] + bbox[2]) / 2
            cy = (bbox[1] + bbox[3]) / 2
            px = (prev_bbox[0] + prev_bbox[2]) / 2
            py = (prev_bbox[1] + prev_bbox[3]) / 2

            # Movement analysis
            speed     = MovementEngine.compute_speed((px, py), (cx, cy), self.fps)
            direction = MovementEngine.compute_direction((px, py), (cx, cy))
            mvmt_res  = MovementEngine.calculate(current_speed=speed)

            # Zone evaluation
            zone_res  = ZoneEngine.evaluate(cx, cy, self.zones)

            # Object interactions (simplified: detect carried bag/backpack)
            interactions = []
            non_person   = [d for d in detections if d["class"] not in ("person",)]
            for obj in non_person:
                ob = obj["bbox"]
                if self._overlaps(bbox, ob):
                    interactions.append("PICKED_UP_OBJECT")
            obj_score = ObjectInteractionEngine.score(interactions)

            # Anomaly scoring
            anomaly_res = AnomalyEngine.calculate(
                speed_deviation=min(1.0, speed / 5.0),
                path_deviation=mvmt_res["movement_score"],
                zone_access_deviation=zone_res["zone_score"],
            )

            # Composite risk
            risk_res = RiskEngine.calculate(
                movement_score=mvmt_res["movement_score"],
                zone_score=zone_res["zone_score"],
                object_score=obj_score,
                anomaly_score=anomaly_res["anomaly_score"],
                crowd_score=crowd_result["crowd_score"],
                weapon_score=self._weapon_score(detections),
            )

            # Threat evaluation
            threat_events = ThreatEngine.evaluate(
                entity_id           = entity_hash,
                camera_id           = self.camera_id,
                location            = self.location,
                tenant_id           = self.tenant_id,
                anomaly_score       = anomaly_res["anomaly_score"] * 100,
                risk_score          = risk_res["risk_score"],
                current_speed       = speed,
                direction           = direction,
                zone_violations     = zone_res["violations"],
                detected_objects    = detections,
                object_interactions = interactions,
                tracking_confidence = 0.9,
            )

            for evt in threat_events:
                evt["explanation"] = ExplainableAIEngine.explain(
                    evt["event_type"], evt["risk_score"]
                )
                all_events.append(evt)
                if on_event:
                    on_event(evt)

            entity_results.append({
                "entity_hash":    entity_hash,
                "track_id":       track_id,
                "bbox":           bbox,
                "center":         [cx, cy],
                "speed":          speed,
                "direction":      direction,
                "risk_score":     risk_res["risk_score"],
                "risk_level":     risk_res["risk_level"],
                "zone_violation": zone_res["in_violation"],
                "anomaly_score":  round(anomaly_res["anomaly_score"] * 100, 1),
            })

        return {
            "camera_id":       self.camera_id,
            "timestamp":       timestamp.isoformat(),
            "frame_b64":       frame_b64,
            "entities":        entity_results,
            "crowd":           crowd_result,
            "events_triggered": all_events,
            "detections":      [
                {"class": d["class"], "confidence": d["confidence"]}
                for d in detections
            ],
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _encode_frame(frame: np.ndarray) -> Optional[str]:
        if frame is None or not CV2_AVAILABLE:
            return None
        import base64
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        if not ok:
            return None
        return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()

    @staticmethod
    def _overlaps(bbox_a: List[int], bbox_b: List[int]) -> bool:
        ax1, ay1, ax2, ay2 = bbox_a
        bx1, by1, bx2, by2 = bbox_b
        return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1

    @staticmethod
    def _weapon_score(detections: List[Dict]) -> float:
        WEAPON_CLASSES = {"knife", "gun", "pistol", "rifle", "firearm", "blade"}
        for d in detections:
            if d["class"].lower() in WEAPON_CLASSES and d["confidence"] > 0.85:
                return 1.0
        return 0.0
