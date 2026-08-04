import os

from pipeline.pipeline import _detect_track_and_pose_in_frames


def detect_track_and_pose_in_frames(input_dir, output_dir, conf_threshold=0.5):
    print(f"input directory: {input_dir}")
    print(f"output directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    detections = _detect_track_and_pose_in_frames(
        input_dir=input_dir,
        output_dir=output_dir,
        conf_threshold=conf_threshold,
        save_annotated_frames=True,
    )

    for detection in detections:
        track_ids = detection["track_ids"]
        keypoints = detection["keypoints"]
        if keypoints is not None and len(keypoints) > 0:
            for i, track_id in enumerate(track_ids):
                person_kpts = keypoints[i]
                nose = person_kpts[0]
                left_eye = person_kpts[1]
                right_eye = person_kpts[2]
                left_shoulder = person_kpts[5]
                right_shoulder = person_kpts[6]
                left_elbow = person_kpts[7]
                right_elbow = person_kpts[8]
                left_wrist = person_kpts[9]
                right_wrist = person_kpts[10]
                left_hip = person_kpts[11]
                right_hip = person_kpts[12]
                left_knee = person_kpts[13]
                right_knee = person_kpts[14]
                left_ankle = person_kpts[15]
                right_ankle = person_kpts[16]
                print(f"Track ID {track_id} | nose: {nose} | eyes: {left_eye}, {right_eye} | Shoulders: {left_shoulder}, {right_shoulder} | elbow: {left_elbow},{right_elbow} | wrist: {left_wrist},{right_wrist} | hip {left_hip},{right_hip} | knee {left_knee},{right_knee} | ankle {left_ankle},{right_ankle}")

    print(f"Done! Pose-annotated images saved to: '{output_dir}'")
    return detections


if __name__ == "__main__":
    frames_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "pipeline_data", "7c30c8ebc6301f79", "frames"))
    output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "person_identification", "model_detected_images", "pose_detected_images"))
    detect_track_and_pose_in_frames(frames_folder, output_folder, conf_threshold=0.35)