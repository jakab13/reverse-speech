rootdir = pwd;
talkersdir = append(rootdir, '/CRM/Talkers/');
filelist = dir(fullfile(talkersdir, '**/*.BIN'));
outrootdir = append(rootdir, '/samples/CRM');
fs = 40000;

for i = 1:length(filelist)
    file = filelist(i);
    [~, ParentFolderName] = fileparts(file.folder);
    talkerID = ParentFolderName(end);
    filepath = append(file.folder, '/', file.name);
    out = readbin(filepath);
    outfilename = append(outrootdir, '/', '0', talkerID, file.name(1:end-4), '.wav'); 
    audiowrite(outfilename, out, fs);
    disp(file.name);
end