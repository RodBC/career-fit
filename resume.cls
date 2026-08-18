\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{resume}[2026/07/14 Minimal resume class]

\LoadClass[11pt]{article}

% Basic page/layout defaults (geometry is set in the .tex)
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\raggedright

% Header data
\newcommand{\name}[1]{\def\@resumeName{#1}}
\newcommand{\address}[1]{\def\@resumeAddress{#1}}
\def\@resumeName{}
\def\@resumeAddress{}

\AtBeginDocument{%
  \begin{center}
    {\LARGE\bfseries \@resumeName}\par
    \vspace{4pt}
    {\small \@resumeAddress}\par
  \end{center}
  \vspace{-6pt}
}

% Section environment used by the template
\newenvironment{rSection}[1]{%
  \vspace{8pt}
  {\large\bfseries #1}\par
  \vspace{3pt}
  \hrule
  \vspace{6pt}
}{%
  \vspace{2pt}
}

