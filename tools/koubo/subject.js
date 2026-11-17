ObjC.import('Foundation'); ObjC.import('Vision'); ObjC.import('CoreImage'); ObjC.import('AppKit');
function run(argv) {
  const [inPath, outPath] = argv;
  const ci = $.CIImage.imageWithContentsOfURL($.NSURL.fileURLWithPath(inPath));
  const handler = $.VNImageRequestHandler.alloc.initWithCIImageOptions(ci, $({}));
  const req = $.VNGenerateForegroundInstanceMaskRequest.alloc.init;
  if (!handler.performRequestsError($([req]), null)) return 'perform failed';
  const obs = req.results.objectAtIndex(0);
  const err = Ref();
  const buf = obs.generateScaledMaskForImageForInstancesFromRequestHandlerError(obs.allInstances, handler, err);
  const m = $.CIImage.imageWithCVPixelBuffer(buf);
  const ok = $.CIContext.context.writePNGRepresentationOfImageToURLFormatColorSpaceOptionsError(m, $.NSURL.fileURLWithPath(outPath), $.kCIFormatL8, $.CGColorSpaceCreateDeviceGray(), $({}), null);
  return `instances ${obs.allInstances.count} ok=${ok}`;
}
