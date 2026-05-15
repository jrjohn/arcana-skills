import Foundation
import Vision
import AppKit

// ocr-mac <image_path>
// Outputs recognized text to stdout. Mixed zh-Hant + en-US, accurate mode.
// Exit codes: 0 ok, 1 bad args, 2 file/load fail, 3 OCR fail.

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write("usage: ocr-mac <image_path>\n".data(using: .utf8)!)
    exit(1)
}

let path = CommandLine.arguments[1]
let url = URL(fileURLWithPath: path)

guard let img = NSImage(contentsOf: url),
      let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    FileHandle.standardError.write("ocr-mac: cannot load image at \(path)\n".data(using: .utf8)!)
    exit(2)
}

let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.recognitionLanguages = ["zh-Hant", "en-US"]
req.usesLanguageCorrection = true
req.automaticallyDetectsLanguage = true

let handler = VNImageRequestHandler(cgImage: cg, options: [:])
do {
    try handler.perform([req])
} catch {
    FileHandle.standardError.write("ocr-mac: OCR failed: \(error)\n".data(using: .utf8)!)
    exit(3)
}

guard let observations = req.results else {
    exit(0)
}

// Preserve reading order: top-to-bottom (Vision uses bottom-origin coords, so sort by -minY).
let sorted = observations.sorted { lhs, rhs in
    if abs(lhs.boundingBox.minY - rhs.boundingBox.minY) > 0.01 {
        return lhs.boundingBox.minY > rhs.boundingBox.minY
    }
    return lhs.boundingBox.minX < rhs.boundingBox.minX
}

var out = ""
for obs in sorted {
    if let cand = obs.topCandidates(1).first {
        out += cand.string
        out += "\n"
    }
}
print(out, terminator: "")
