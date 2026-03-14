import { useEffect, useRef, useState } from "react";

export default function WebcamCapture() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [photo, setPhoto] = useState<string | null>(null);
  const [countdown, setCountdown] = useState<number>(5);

  useEffect(() => {
    const startWebcam = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (error) {
        console.error(error);
      }
    };

    startWebcam();
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev === 1) {
          capturePhoto();
          return 5; // reset countdown
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const capturePhoto = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL("image/png");
    setPhoto(dataUrl);
  };

  return (
    <div className="flex items-center justify-center gap-5">
      
      {/* Video container */}
      <div className="relative w-[320px] h-[240px] border-black rounded-sm border-2 overflow-hidden">
        
        <video
          ref={videoRef}
          autoPlay
          className="w-full h-full object-cover"
        />

        {/* Countdown overlay */}
        <div className="absolute inset-0 flex items-center justify-center text-white text-6xl font-bold bg-black/20">
          {countdown}
        </div>

      </div>

      <canvas
        ref={canvasRef}
        width={320}
        height={240}
        style={{ display: "none" }}
      />

      <div className="w-[320px] h-[240px] overflow-hidden border-black rounded-sm bg-black border-2">
        {photo && (
          <img
            className="w-full h-full object-cover"
            src={photo}
            alt="Latest photo"
          />
        )}
      </div>
    </div>
  );
}