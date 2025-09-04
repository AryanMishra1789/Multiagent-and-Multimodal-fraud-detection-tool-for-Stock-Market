import { useState } from "react";
import {
  FileText,
  Upload,
  Mic,
  Video,
  CheckCircle,
  AlertTriangle,
  Clock,
  X,
  Building,
  Shield,
  Info,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/use-toast";
import { apiService, VerificationResult, DocumentVerificationResult, handleApiError } from "@/lib/api";

export default function ContentVerification() {
  const [textContent, setTextContent] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<VerificationResult | DocumentVerificationResult | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isVerifyingDocument, setIsVerifyingDocument] = useState(false);
  const [activeTab, setActiveTab] = useState("text");
  const { toast } = useToast();

  // Clear verification result when switching tabs
  const handleTabChange = (value: string) => {
    setActiveTab(value);
    setVerificationResult(null);
  };

  const handleTextVerification = async () => {
    if (!textContent.trim()) {
      toast({
        title: "Error",
        description: "Please enter some text to verify",
        variant: "destructive",
      });
      return;
    }

    setIsVerifying(true);
    try {
      const result = await apiService.verifyText(textContent);
      setVerificationResult(result);
      
      toast({
        title: "Verification Complete",
        description: `Content classified as ${result.classification || 'analyzed'}`,
      });
    } catch (error) {
      const errorMessage = handleApiError(error);
      toast({
        title: "Verification Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>, type: string) => {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;

    const file = files[0];
    setUploadedFiles([file]);

    if (type === "document") {
      setIsVerifyingDocument(true);
      try {
        const result = await apiService.verifyDocument(file);
        setVerificationResult(result);
        
        toast({
          title: "Document Verification Complete",
          description: "Document has been analyzed for potential fraud indicators",
        });
      } catch (error) {
        const errorMessage = handleApiError(error);
        toast({
          title: "Document Verification Failed",
          description: errorMessage,
          variant: "destructive",
        });
      } finally {
        setIsVerifyingDocument(false);
      }
    }
  };

  const removeFile = (index: number) => {
    setUploadedFiles(files => files.filter((_, i) => i !== index));
  };

  // Type guard to check if result is VerificationResult
  const isVerificationResult = (result: VerificationResult | DocumentVerificationResult): result is VerificationResult => {
    return 'classification' in result;
  };

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="text">Text Verification</TabsTrigger>
          <TabsTrigger value="document">Document Upload</TabsTrigger>
          <TabsTrigger value="media">Media Upload</TabsTrigger>
        </TabsList>

        {/* Text Verification */}
        <TabsContent value="text" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Text Content Verification
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Enter text content to verify for potential fraud indicators..."
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                className="min-h-[200px]"
              />
              <Button 
                onClick={handleTextVerification} 
                disabled={isVerifying || !textContent.trim()}
                className="w-full"
              >
                {isVerifying ? (
                  <>
                    <Clock className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing Content...
                  </>
                ) : (
                  <>
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Verify Content
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Document Upload */}
        <TabsContent value="document" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Document Verification
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/50 transition-colors">
                <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-lg font-medium mb-2">Upload Documents</p>
                <p className="text-sm text-muted-foreground mb-4">
                  PDF, DOC, DOCX, TXT files up to 10MB
                </p>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={(e) => handleFileUpload(e, "document")}
                  className="hidden"
                  id="document-upload"
                />
                <Button 
                  variant="outline" 
                  onClick={() => document.getElementById("document-upload")?.click()}
                  disabled={isVerifyingDocument}
                >
                  {isVerifyingDocument ? (
                    <>
                      <Clock className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    "Choose Files"
                  )}
                </Button>
              </div>

              {uploadedFiles.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium">Uploaded Files:</h4>
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText className="h-4 w-4" />
                        <span className="text-sm">{file.name}</span>
                        <span className="text-xs text-muted-foreground">
                          ({(file.size / 1024 / 1024).toFixed(2)} MB)
                        </span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(index)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Media Upload */}
        <TabsContent value="media" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Audio/Video Verification</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border-2 border-dashed border-border rounded-lg p-6 text-center hover:border-primary/50 transition-colors">
                  <Mic className="mx-auto h-8 w-8 text-muted-foreground mb-3" />
                  <p className="text-sm font-medium">Upload Audio Files</p>
                  <p className="text-xs text-muted-foreground">MP3, WAV, M4A up to 50MB</p>
                  <input
                    type="file"
                    accept=".mp3,.wav,.m4a"
                    onChange={(e) => handleFileUpload(e, "audio")}
                    className="hidden"
                    id="audio-upload"
                  />
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => document.getElementById("audio-upload")?.click()}
                    className="mt-3"
                  >
                    Choose Audio Files
                  </Button>
                </div>

                <div className="border-2 border-dashed border-border rounded-lg p-6 text-center hover:border-primary/50 transition-colors">
                  <Video className="mx-auto h-8 w-8 text-muted-foreground mb-3" />
                  <p className="text-sm font-medium">Upload Video Files</p>
                  <p className="text-xs text-muted-foreground">MP4, AVI, MOV up to 100MB</p>
                  <input
                    type="file"
                    accept=".mp4,.avi,.mov"
                    onChange={(e) => handleFileUpload(e, "video")}
                    className="hidden"
                    id="video-upload"
                  />
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => document.getElementById("video-upload")?.click()}
                    className="mt-3"
                  >
                    Choose Video Files
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Verification Results */}
      {verificationResult && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {verificationResult.is_suspicious ? (
                <AlertTriangle className="h-5 w-5 text-red-500" />
              ) : (
                <CheckCircle className="h-5 w-5 text-green-500" />
              )}
              Detailed Verification Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Main Result Summary */}
            <div className={`p-4 rounded-lg border-l-4 ${
              verificationResult.is_suspicious 
                ? 'border-l-red-500 bg-red-50' 
                : 'border-l-green-500 bg-green-50'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-lg">
                  {isVerificationResult(verificationResult) && verificationResult.verification_status ? 
                    verificationResult.verification_status : 
                    (verificationResult.is_suspicious ? 'Suspicious Content Detected' : 'Content Appears Legitimate')
                  }
                </span>
                <Badge variant={verificationResult.is_suspicious ? "destructive" : "default"}>
                  Risk Score: {verificationResult.risk_score || 0}/100
                </Badge>
              </div>
              <p className="text-sm text-gray-700 mb-2">{verificationResult.message || 'Analysis completed'}</p>
              <p className="text-sm font-medium">
                <strong>Analysis Reason:</strong> {verificationResult.reason || 'No specific reason provided'}
              </p>
            </div>

            {/* Classification & Technical Details */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {isVerificationResult(verificationResult) && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-sm text-gray-600 mb-1">Classification</h4>
                  <Badge variant="outline" className={
                    verificationResult.classification === 'SCAM' ? 'border-red-500 text-red-700' :
                    verificationResult.classification === 'NEWS' ? 'border-blue-500 text-blue-700' :
                    'border-gray-500 text-gray-700'
                  }>
                    {verificationResult.classification || 'UNKNOWN'}
                  </Badge>
                </div>
              )}
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-sm text-gray-600 mb-1">Processing Time</h4>
                <p className="text-sm">{verificationResult.processing_time || 0}ms</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-sm text-gray-600 mb-1">Analysis Date</h4>
                <p className="text-sm">
                  {verificationResult.timestamp ? 
                    (() => {
                      try {
                        return new Date(verificationResult.timestamp).toLocaleString();
                      } catch (e) {
                        return 'Just now';
                      }
                    })() : 
                    'Just now'
                  }
                </p>
              </div>
            </div>

            {/* Companies Analysis - Only for VerificationResult */}
            {isVerificationResult(verificationResult) && 
             Array.isArray(verificationResult.verified_companies) && verificationResult.verified_companies.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Building className="h-5 w-5" />
                  Verified Companies
                </h3>
                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <ul className="text-sm space-y-1">
                    {verificationResult.verified_companies.map((company, index) => (
                      <li key={index} className="text-green-700">• {String(company)}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {isVerificationResult(verificationResult) && 
             Array.isArray(verificationResult.suspicious_companies) && verificationResult.suspicious_companies.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" />
                  Suspicious Companies
                </h3>
                <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                  <ul className="text-sm space-y-1">
                    {verificationResult.suspicious_companies.map((company, index) => (
                      <li key={index} className="text-red-700">• {String(company)}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* SEBI Regulatory Analysis */}
            {isVerificationResult(verificationResult) && verificationResult.sebi_rag && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  SEBI Regulatory Analysis
                </h3>
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-sm text-blue-800">{String(verificationResult.sebi_rag)}</p>
                </div>
              </div>
            )}

            {/* Analysis Summary */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Analysis Summary
              </h3>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="space-y-3">
                  {isVerificationResult(verificationResult) && (
                    <div className="flex items-start gap-2">
                      <span className="font-medium text-sm">Classification:</span>
                      <span className="text-sm">{verificationResult.classification || 'Unknown'}</span>
                    </div>
                  )}
                  <div className="flex items-start gap-2">
                    <span className="font-medium text-sm">Risk Assessment:</span>
                    <span className="text-sm">
                      {(verificationResult.risk_score || 0) >= 70 ? 'High Risk' : 
                       (verificationResult.risk_score || 0) >= 40 ? 'Medium Risk' : 'Low Risk'} 
                      ({verificationResult.risk_score || 0}/100)
                    </span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="font-medium text-sm">Recommendation:</span>
                    <span className="text-sm">
                      {verificationResult.is_suspicious ? 
                        'Immediate investigation required. Content shows signs of fraudulent activity.' :
                        'Content appears legitimate. Continue routine monitoring.'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Regulatory Disclaimer */}
            <div className="mt-6 p-4 bg-gray-100 rounded-lg border">
              <h4 className="font-medium text-gray-800 mb-2 flex items-center gap-2">
                <Info className="h-4 w-4" />
                Regulatory Notice
              </h4>
              <p className="text-sm text-muted-foreground">
                This analysis was conducted using AI-powered fraud detection algorithms in compliance with SEBI guidelines. 
                The reasoning provided is based on pattern recognition, sentiment analysis, and regulatory database cross-referencing. 
                For critical decisions, manual verification by authorized personnel is recommended.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
